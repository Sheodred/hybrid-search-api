"""Hybrid search: combines classic BM25 full-text search with kNN vector search
using Reciprocal Rank Fusion (RRF) - a simple, well-established way to merge two
ranked lists without needing to hand-tune score weights.

The actual query DSL ("how a search request is phrased") lives in queries.py;
this module only orchestrates and fuses the results.
"""

from elasticsearch import Elasticsearch

from hybrid_search_api.search.queries import bm25_query, knn_query

RRF_K = 60  # standard constant from the RRF paper; higher = flatter weighting


def _bm25_search(client: Elasticsearch, index: str, query: str, size: int) -> list[dict]:
    resp = client.search(index=index, query=bm25_query(query), size=size)
    return list(resp["hits"]["hits"])


def _knn_search(
    client: Elasticsearch, index: str, query_vector: list[float], size: int
) -> list[dict]:
    resp = client.search(index=index, knn=knn_query(query_vector, size), size=size)
    return list(resp["hits"]["hits"])


def _reciprocal_rank_fusion(*ranked_lists: list[dict]) -> list[dict]:
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}
    for ranked in ranked_lists:
        for rank, hit in enumerate(ranked):
            doc_id = hit["_id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank + 1)
            docs[doc_id] = hit
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [{**docs[doc_id], "_rrf_score": score} for doc_id, score in ordered]


def hybrid_search(
    client: Elasticsearch,
    index: str,
    query: str,
    query_vector: list[float] | None = None,
    size: int = 10,
) -> list[dict]:
    """Run BM25 (+ optionally kNN) search and fuse the results with RRF.

    Falls back to pure BM25 if no query_vector is supplied - keeps the function
    usable before an embedding model is wired in.
    """
    bm25_hits = _bm25_search(client, index, query, size)
    if query_vector is None:
        return bm25_hits
    knn_hits = _knn_search(client, index, query_vector, size)
    return _reciprocal_rank_fusion(bm25_hits, knn_hits)[:size]
