"""Hybrid search: combines classic BM25 full-text search with kNN vector search
using Reciprocal Rank Fusion (RRF) - a simple, well-established way to merge two
ranked lists without needing to hand-tune score weights.

The actual query DSL ("how a search request is phrased") lives in queries.py;
this module only orchestrates, fuses, and parses the response.

RRF runs here in Python rather than through Elasticsearch's native `rrf`
retriever because that retriever is licensed and returns 403 on a basic
license - see docs/adr/0003-elasticsearch-9-upgrade.md. The formula is
`score(doc) = sum over lists of 1 / (RRF_RANK_CONSTANT + rank)`.
"""

from dataclasses import dataclass

from elasticsearch import Elasticsearch

from hybrid_search_api.models import FacetBucket, SearchFilters, WordCountStats
from hybrid_search_api.search.queries import (
    RRF_RANK_CONSTANT,
    bm25_query,
    facet_aggs,
    highlight_config,
    knn_query,
)

# The embedding is 384 floats per document - useful to search, pure noise in a
# response body. Excluded on every call.
SOURCE_EXCLUDES = ["embedding"]


@dataclass
class HybridResult:
    """What one search returns: the fused hits plus the aggregation-derived
    facets. Facets are None when the caller's Elasticsearch response carried
    no aggregations."""

    hits: list[dict]
    facets: dict[str, list[FacetBucket]] | None = None
    word_count_stats: WordCountStats | None = None


def _bm25_search(
    client: Elasticsearch, index: str, query: str, size: int, filters: SearchFilters | None
) -> dict:
    # Highlighting and aggregations ride on this call only. Aggregations are
    # computed over everything matching the query under the active filters,
    # so the buckets describe the BM25 match set - not the fused ranking.
    # Running them on the kNN call too would just produce a second bucket set
    # to reconcile. See docs/search/README.md.
    return client.search(
        index=index,
        query=bm25_query(query, filters),
        size=size,
        highlight=highlight_config(),
        aggs=facet_aggs(),
        source_excludes=SOURCE_EXCLUDES,
    )


def _knn_search(
    client: Elasticsearch,
    index: str,
    query_vector: list[float],
    size: int,
    filters: SearchFilters | None,
) -> list[dict]:
    resp = client.search(
        index=index,
        knn=knn_query(query_vector, size, filters),
        size=size,
        source_excludes=SOURCE_EXCLUDES,
    )
    return list(resp["hits"]["hits"])


def _reciprocal_rank_fusion(*ranked_lists: list[dict]) -> list[dict]:
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}
    for ranked in ranked_lists:
        for rank, hit in enumerate(ranked):
            doc_id = hit["_id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_RANK_CONSTANT + rank + 1)
            # Merge rather than overwrite, keeping whatever the first list to
            # produce this document supplied. Only the BM25 call asks for
            # highlights, so a plain `docs[doc_id] = hit` would strip the
            # snippet off every document that also came back from the kNN
            # call - precisely the documents RRF ranks highest.
            docs[doc_id] = {**hit, **docs.get(doc_id, {})}
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [{**docs[doc_id], "_rrf_score": score} for doc_id, score in ordered]


def _parse_facets(aggregations: dict) -> dict[str, list[FacetBucket]]:
    """Bucket aggregations -> facet lists. `stats` is handled separately."""
    facets: dict[str, list[FacetBucket]] = {}
    for name, agg in aggregations.items():
        buckets = agg.get("buckets")
        if buckets is None:  # stats agg, or anything else that isn't bucketed
            continue
        facets[name] = [
            # date_histogram reports the bucket as epoch millis in "key" and a
            # formatted date in "key_as_string" - prefer the readable one.
            FacetBucket(key=b.get("key_as_string", b["key"]), doc_count=b["doc_count"])
            for b in buckets
        ]
    return facets


def _parse_word_count_stats(aggregations: dict) -> WordCountStats | None:
    stats = aggregations.get("word_count")
    if stats is None or "count" not in stats:
        return None
    return WordCountStats(
        count=stats["count"], min=stats.get("min"), max=stats.get("max"), avg=stats.get("avg")
    )


def hybrid_search(
    client: Elasticsearch,
    index: str,
    query: str,
    query_vector: list[float] | None = None,
    size: int = 10,
    filters: SearchFilters | None = None,
) -> HybridResult:
    """Run BM25 (+ optionally kNN) search and fuse the results with RRF.

    Falls back to pure BM25 if no query_vector is supplied - keeps the function
    usable when the embedding model is unavailable.
    """
    bm25_resp = _bm25_search(client, index, query, size, filters)
    bm25_hits = list(bm25_resp["hits"]["hits"])
    aggregations = bm25_resp.get("aggregations") or {}

    if query_vector is None:
        hits = bm25_hits
    else:
        knn_hits = _knn_search(client, index, query_vector, size, filters)
        hits = _reciprocal_rank_fusion(bm25_hits, knn_hits)[:size]

    return HybridResult(
        hits=hits,
        facets=_parse_facets(aggregations) or None,
        word_count_stats=_parse_word_count_stats(aggregations),
    )
