import logging

from anthropic import AuthenticationError, NotFoundError
from fastapi import APIRouter, Depends, HTTPException

from hybrid_search_api.ai.llm_client import LLMClient
from hybrid_search_api.ai.prompts import build_rag_prompt
from hybrid_search_api.config import Settings, get_settings
from hybrid_search_api.models import SearchHit, SearchRequest, SearchResponse
from hybrid_search_api.search.elasticsearch_client import build_client
from hybrid_search_api.search.embeddings import embed
from hybrid_search_api.search.hybrid_search import hybrid_search

logger = logging.getLogger(__name__)
router = APIRouter()


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
        "passed to the configured Anthropic model to synthesize a short, source-grounded "
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
        system, prompt = build_rag_prompt(request.query, [h.model_dump() for h in hits])
        try:
            answer = llm.complete(system=system, prompt=prompt)
        except AuthenticationError as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Anthropic hat den API-Key abgelehnt. Pruefe ANTHROPIC_API_KEY in .env "
                    "(evtl. noch der Platzhalter aus .env.example?)."
                ),
            ) from exc
        except NotFoundError as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"Anthropic-Modell '{settings.anthropic_model}' wurde nicht gefunden. "
                    "Pruefe ANTHROPIC_MODEL in .env."
                ),
            ) from exc

    return SearchResponse(query=request.query, hits=hits, answer=answer)
