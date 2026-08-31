"""Elasticsearch query templates - the "prepared statements" for search.

Every function here returns a plain query-DSL dict: the actual phrasing of
a search request against Elasticsearch. This is the one place to tune how
a query is built (field boosts, fuzziness, candidate-pool size, ...) without
touching the RRF/orchestration logic in hybrid_search.py.

The split that matters here is **query context vs. filter context**:

- Query context ("must" / "should") asks *how well* a document matches and
  contributes to the score.
- Filter context ("filter") asks *whether* a document may match at all. It
  contributes no score and Elasticsearch caches it. Every metadata narrowing
  goes here, and the same clauses are handed to the kNN side as a
  **pre-filter**, so both halves of hybrid search see the identical subset.

Rendered examples of these query bodies live in docs/search/example_*.json,
kept in sync by tests/test_config_snapshots.py, and explained one by one in
docs/search/README.md.
"""

from hybrid_search_api.models import SearchFilters

# Boost title matches over content matches. Raise/lower to shift how much a
# term hit in the title outweighs a hit in the body text.
TITLE_BOOST = 3

# How many kNN candidates are gathered per shard, relative to how many
# results are requested (k * KNN_CANDIDATE_MULTIPLIER). Higher = more
# accurate nearest-neighbor results but slower search.
KNN_CANDIDATE_MULTIPLIER = 5

# An exact phrase match is strong evidence, so it earns a score bonus on top
# of the term-level match. PHRASE_SLOP allows that many words to sit between
# the query terms and still count as a phrase.
PHRASE_BOOST = 2
PHRASE_SLOP = 2

# With most_fields and fuzziness, a long query would otherwise match documents
# sharing only a term or two. Requiring 75% of the terms keeps recall sane.
MIN_SHOULD_MATCH = "75%"

# Standard constant from the RRF paper; higher = flatter weighting.
# Lives here with the other tuning knobs; the fusion itself is in
# hybrid_search.py (the native rrf retriever is licensed - see ADR-0003).
RRF_RANK_CONSTANT = 60


def text_query(query_text: str) -> dict:
    """The scoring half of a search: term matching plus a phrase bonus.

    `most_fields` (rather than the default `best_fields`) sums the per-field
    scores instead of taking the best one, which suits the same text being
    searchable through several analyses - `title`, `content`, and the
    `copy_to` catch-all `all_text`.

    The `should` clause is where `.exact` earns its place: the main fields are
    stemmed and stopworded, so a phrase query against them would match a
    looser wording than the user typed. `content.exact` keeps the literal
    tokens, so this rewards documents that contain the actual phrase.
    """
    return {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "query": query_text,
                        "type": "most_fields",
                        "fields": [f"title^{TITLE_BOOST}", "content", "all_text"],
                        "minimum_should_match": MIN_SHOULD_MATCH,
                        "fuzziness": "AUTO",
                    }
                }
            ],
            "should": [
                {
                    "match_phrase": {
                        "content.exact": {
                            "query": query_text,
                            "slop": PHRASE_SLOP,
                            "boost": PHRASE_BOOST,
                        }
                    }
                }
            ],
        }
    }


def filter_clauses(filters: SearchFilters | None) -> list[dict]:
    """Translate the request's filters into filter-context clauses.

    Returns [] when nothing is set, which callers can drop into a `bool`
    unchanged - an empty filter list matches everything.

    Dates are emitted as ISO strings rather than `date` objects so the result
    is a plain JSON-serializable dict (the snapshot test renders it verbatim).
    """
    if filters is None:
        return []

    clauses: list[dict] = []
    for field, values in (
        ("category", filters.category),
        ("tags", filters.tags),
        ("source", filters.source),
    ):
        if values:
            clauses.append({"terms": {field: values}})

    published: dict[str, str] = {}
    if filters.published_after:
        published["gte"] = filters.published_after.isoformat()
    if filters.published_before:
        published["lte"] = filters.published_before.isoformat()
    if published:
        clauses.append({"range": {"published": published}})

    word_count: dict[str, int] = {}
    if filters.min_word_count is not None:
        word_count["gte"] = filters.min_word_count
    if filters.max_word_count is not None:
        word_count["lte"] = filters.max_word_count
    if word_count:
        clauses.append({"range": {"word_count": word_count}})

    return clauses


def bm25_query(query_text: str, filters: SearchFilters | None = None) -> dict:
    """Full BM25 side: the scoring query narrowed by filter context."""
    query = text_query(query_text)
    clauses = filter_clauses(filters)
    if clauses:
        query["bool"]["filter"] = clauses
    return query


def knn_query(query_vector: list[float], k: int, filters: SearchFilters | None = None) -> dict:
    """kNN vector search against the 'embedding' field.

    The `filter` here is a **pre-filter**: Elasticsearch applies it before the
    approximate search, so `num_candidates` is drawn from the filtered subset.
    Post-filtering instead would search the whole index and then discard most
    of what it found, which can leave far fewer than k results.
    """
    query = {
        "field": "embedding",
        "query_vector": query_vector,
        "k": k,
        "num_candidates": k * KNN_CANDIDATE_MULTIPLIER,
    }
    clauses = filter_clauses(filters)
    if clauses:
        query["filter"] = {"bool": {"filter": clauses}}
    return query


def highlight_config() -> dict:
    """Snippets for the matched part of `content`.

    The `unified` highlighter reuses the `term_vector: with_positions_offsets`
    stored on `content` (see index_config.py) instead of re-analyzing the
    field, which is what makes it cheap on long documents.
    """
    return {
        "fields": {
            "content": {
                "type": "unified",
                "fragment_size": 150,
                "number_of_fragments": 2,
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"],
            }
        }
    }


def facet_aggs() -> dict:
    """Aggregations backing the response's facets.

    Three shapes on purpose: `terms` for categorical buckets, `date_histogram`
    for a time axis, `stats` for a numeric summary.
    """
    return {
        "categories": {"terms": {"field": "category", "size": 20}},
        "tags": {"terms": {"field": "tags", "size": 20}},
        "by_month": {
            "date_histogram": {
                "field": "published",
                "calendar_interval": "month",
                "min_doc_count": 1,
            }
        },
        "word_count": {"stats": {"field": "word_count"}},
    }


def recency_boosted_query(query_text: str) -> dict:
    """Reference only - not called by the running search path.

    Shows score shaping: a `gauss` decay on `published` multiplies the
    relevance score by a factor that falls off smoothly with age, so a
    slightly-less-relevant recent document can outrank a stale one. `scale`
    is the distance from `origin` at which the factor reaches `decay` - here,
    a two-year-old document keeps half its score.

    `scale` has to match the corpus's actual age spread. At the more typical
    "180d" every document in this demo set (published 2023-2025) decays to
    effectively zero, and the ranking becomes noise dressed up as recency.

    Left out of `/search` deliberately: recency bias is a product decision,
    and this corpus has no freshness requirement. Rendered to
    docs/search/example_function_score_recency.json so the shape is readable.
    """
    return {
        "function_score": {
            "query": text_query(query_text),
            "functions": [
                {
                    "gauss": {
                        "published": {
                            "origin": "now",
                            "scale": "730d",
                            "offset": "30d",
                            "decay": 0.5,
                        }
                    }
                }
            ],
            "boost_mode": "multiply",
        }
    }
