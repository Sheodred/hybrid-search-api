"""Owns the /search request end to end: builds the ES client, embeds the query
(falling back to BM25-only if that fails), runs hybrid search, and - if asked -
synthesizes a RAG answer. Framework-agnostic: raises the LLM SDK's own
exceptions unchanged rather than FastAPI's HTTPException, so the caller (the
route) decides how to translate them into HTTP.
"""

import logging

from hybrid_search_api.ai.llm_client import LLMClient
from hybrid_search_api.ai.prompts import build_rag_prompt
from hybrid_search_api.config import Settings, resolve_index
from hybrid_search_api.models import SearchHit, SearchRequest, SearchResponse
from hybrid_search_api.search.agentic_answering import agentic_answer_search
from hybrid_search_api.search.elasticsearch_client import build_client
from hybrid_search_api.search.embeddings import embed
from hybrid_search_api.search.hybrid_search import hybrid_search

logger = logging.getLogger(__name__)


def _extract_score(hit: dict) -> float:
    # After RRF fusion the hit still carries its original per-list _score
    # (BM25 or kNN) alongside the fused _rrf_score it was actually ranked by -
    # prefer the fused score so the displayed value matches the ranking.
    score = hit.get("_rrf_score")
    return score if score is not None else hit.get("_score", 0.0)


def _rag_context(hit: SearchHit) -> dict:
    """Passage-based RAG: feed the model the matching snippets rather than the
    whole document when highlighting found any.

    Shorter, better-targeted context costs fewer tokens and keeps the model's
    attention on the part that actually matched. Hits found only by the vector
    side have no highlights and fall back to full content."""
    context = hit.model_dump()
    if hit.highlights:
        context["content"] = " ... ".join(hit.highlights)
    return context


def answer_search(
    request: SearchRequest, settings: Settings, llm_client: LLMClient | None = None
) -> SearchResponse:
    if request.agentic:
        return agentic_answer_search(request, settings, llm_client)

    es_client = build_client(settings)

    try:
        query_vector = embed(request.query)
    except Exception:
        logger.exception("Embedding model unavailable, falling back to BM25-only search")
        query_vector = None

    result = hybrid_search(
        client=es_client,
        index=resolve_index(settings, request.dataset),
        query=request.query,
        query_vector=query_vector,
        size=request.top_k,
        filters=request.filters,
    )
    hits = [
        SearchHit(
            id=h["_id"],
            score=_extract_score(h),
            title=h["_source"].get("title", ""),
            content=h["_source"].get("content", ""),
            highlights=h.get("highlight", {}).get("content"),
        )
        for h in result.hits
    ]

    answer = None
    if request.use_llm_answer and hits:
        llm = llm_client if llm_client is not None else LLMClient(settings)
        system, prompt = build_rag_prompt(
            request.query, [_rag_context(h) for h in hits], lang=request.lang
        )
        answer = llm.complete(system=system, prompt=prompt)

    return SearchResponse(
        query=request.query,
        hits=hits,
        answer=answer,
        facets=result.facets,
        word_count_stats=result.word_count_stats,
    )
