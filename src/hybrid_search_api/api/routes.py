import logging

from fastapi import APIRouter, Depends, HTTPException
from openai import APIError, APIStatusError, AuthenticationError, NotFoundError

from hybrid_search_api.ai.llm_client import LLMClient
from hybrid_search_api.ai.prompts import build_rag_prompt
from hybrid_search_api.config import Settings, get_settings
from hybrid_search_api.models import SearchHit, SearchRequest, SearchResponse
from hybrid_search_api.search.elasticsearch_client import build_client
from hybrid_search_api.search.embeddings import embed
from hybrid_search_api.search.hybrid_search import hybrid_search

logger = logging.getLogger(__name__)
router = APIRouter()

_ERROR_MESSAGES = {
    "auth": {
        "en": "The LLM endpoint rejected the API key. Check LLM_API_KEY (and LLM_BASE_URL, if set) in .env.",
        "de": (
            "Der LLM-Endpunkt hat den API-Key abgelehnt. Pruefe LLM_API_KEY "
            "(und ggf. LLM_BASE_URL) in .env."
        ),
    },
    "not_found": {
        "en": "Model '{model}' was not found at the configured endpoint. Check LLM_MODEL in .env.",
        "de": (
            "Modell '{model}' wurde am konfigurierten Endpunkt nicht "
            "gefunden. Pruefe LLM_MODEL in .env."
        ),
    },
    "api_status": {
        "en": "LLM endpoint responded with error {status}: {message}",
        "de": "LLM-Endpunkt antwortete mit Fehler {status}: {message}",
    },
    "unreachable": {
        "en": "LLM endpoint not reachable ({base_url}): {error}",
        "de": "LLM-Endpunkt nicht erreichbar ({base_url}): {error}",
    },
}


def _extract_score(hit: dict) -> float:
    score = hit.get("_score")
    return score if score is not None else hit.get("_rrf_score", 0.0)


@router.get("/health", tags=["ops"], summary="Liveness check")
def health() -> dict:
    return {"status": "ok"}


@router.post(
    "/search",
    response_model=SearchResponse,
    tags=["search"],
    summary="Hybrid search with optional RAG answer",
    description=(
        "Runs BM25 + kNN hybrid search (fused via Reciprocal Rank Fusion) against the "
        "configured Elasticsearch index. If `use_llm_answer` is true, the top hits are "
        "passed to the configured LLM to synthesize a short, source-grounded "
        "answer."
    ),
)
def search(request: SearchRequest, settings: Settings = Depends(get_settings)) -> SearchResponse:
    es_client = build_client(settings)

    try:
        query_vector = embed(request.query)
    except Exception:
        logger.exception("Embedding model unavailable, falling back to BM25-only search")
        query_vector = None

    raw_hits = hybrid_search(
        client=es_client,
        index=settings.elasticsearch_index,
        query=request.query,
        query_vector=query_vector,
        size=request.top_k,
    )
    hits = [
        SearchHit(
            id=h["_id"],
            score=_extract_score(h),
            title=h["_source"].get("title", ""),
            content=h["_source"].get("content", ""),
        )
        for h in raw_hits
    ]

    answer = None
    if request.use_llm_answer and hits:
        llm = LLMClient(settings)
        system, prompt = build_rag_prompt(
            request.query, [h.model_dump() for h in hits], lang=request.lang
        )
        try:
            answer = llm.complete(system=system, prompt=prompt)
        except AuthenticationError as exc:
            raise HTTPException(
                status_code=502,
                detail=_ERROR_MESSAGES["auth"][request.lang],
            ) from exc
        except NotFoundError as exc:
            raise HTTPException(
                status_code=502,
                detail=_ERROR_MESSAGES["not_found"][request.lang].format(model=settings.llm_model),
            ) from exc
        except APIStatusError as exc:
            # Catches everything else the endpoint answered with an HTTP error for
            # (429 rate limit, 400 bad request, 5xx on the gateway's own side, ...).
            raise HTTPException(
                status_code=502,
                detail=_ERROR_MESSAGES["api_status"][request.lang].format(
                    status=exc.status_code, message=exc.message
                ),
            ) from exc
        except APIError as exc:
            # No HTTP response at all - connection refused, DNS failure, timeout,
            # TLS problem, etc. Usually means LLM_BASE_URL is wrong or unreachable.
            raise HTTPException(
                status_code=502,
                detail=_ERROR_MESSAGES["unreachable"][request.lang].format(
                    base_url=settings.llm_base_url, error=exc
                ),
            ) from exc

    return SearchResponse(query=request.query, hits=hits, answer=answer)
