"""Elasticsearch query templates - the "prepared statements" for search.

Every function here returns a plain query-DSL dict: the actual phrasing of
a search request against Elasticsearch. This is the one place to tune how
a query is built (field boosts, fuzziness, candidate-pool size, ...) without
touching the RRF/orchestration logic in hybrid_search.py.
"""

# Boost title matches over content matches (2x weight). Raise/lower to shift
# how much a term hit in the title outweighs a hit in the body text.
TITLE_BOOST = 2

# How many kNN candidates are gathered per shard, relative to how many
# results are requested (k * KNN_CANDIDATE_MULTIPLIER). Higher = more
# accurate nearest-neighbor results but slower search.
KNN_CANDIDATE_MULTIPLIER = 5


def bm25_query(query_text: str) -> dict:
    """Classic full-text query: multi_match across title (boosted) and content.

    fuzziness="AUTO" tolerates small typos (e.g. "Elastisearch" still matches
    "Elasticsearch") - remove it if exact matching is preferred.
    """
    return {
        "multi_match": {
            "query": query_text,
            "fields": [f"title^{TITLE_BOOST}", "content"],
            "fuzziness": "AUTO",
        }
    }


def knn_query(query_vector: list[float], k: int) -> dict:
    """kNN vector search against the 'embedding' field."""
    return {
        "field": "embedding",
        "query_vector": query_vector,
        "k": k,
        "num_candidates": k * KNN_CANDIDATE_MULTIPLIER,
    }
