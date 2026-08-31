from hybrid_search_api.models import SearchFilters
from hybrid_search_api.search.queries import (
    KNN_CANDIDATE_MULTIPLIER,
    MIN_SHOULD_MATCH,
    PHRASE_BOOST,
    RRF_RANK_CONSTANT,
    TITLE_BOOST,
    bm25_query,
    facet_aggs,
    filter_clauses,
    highlight_config,
    knn_query,
    recency_boosted_query,
    text_query,
)

FILTERS = SearchFilters(
    category=["vector-search"],
    tags=["hnsw"],
    published_after="2024-01-01",
    published_before="2025-01-01",
    min_word_count=40,
    max_word_count=200,
)


def test_text_query_boosts_title_and_allows_typos():
    q = text_query("Vektorsuche")["bool"]

    multi_match = q["must"][0]["multi_match"]
    assert multi_match["query"] == "Vektorsuche"
    assert multi_match["fields"] == [f"title^{TITLE_BOOST}", "content", "all_text"]
    assert multi_match["type"] == "most_fields"
    assert multi_match["fuzziness"] == "AUTO"
    assert multi_match["minimum_should_match"] == MIN_SHOULD_MATCH


def test_text_query_rewards_exact_phrases_via_unstemmed_subfield():
    should = text_query("vector search")["bool"]["should"]

    phrase = should[0]["match_phrase"]["content.exact"]
    assert phrase["query"] == "vector search"
    assert phrase["boost"] == PHRASE_BOOST
    assert phrase["slop"] >= 0


def test_filter_clauses_is_empty_without_filters():
    assert filter_clauses(None) == []
    assert filter_clauses(SearchFilters()) == []


def test_filter_clauses_covers_terms_and_ranges():
    clauses = filter_clauses(FILTERS)

    assert {"terms": {"category": ["vector-search"]}} in clauses
    assert {"terms": {"tags": ["hnsw"]}} in clauses
    # dates render as ISO strings, not date objects, so the dict stays
    # JSON-serializable for the snapshot
    assert {"range": {"published": {"gte": "2024-01-01", "lte": "2025-01-01"}}} in clauses
    assert {"range": {"word_count": {"gte": 40, "lte": 200}}} in clauses


def test_bm25_query_puts_narrowing_in_filter_context_not_must():
    q = bm25_query("vector search", FILTERS)["bool"]

    # filter context contributes no score - that's the point of putting the
    # metadata narrowing there rather than in must
    assert q["filter"] == filter_clauses(FILTERS)
    assert len(q["must"]) == 1
    assert "multi_match" in q["must"][0]


def test_bm25_query_omits_filter_key_when_unfiltered():
    assert "filter" not in bm25_query("vector search")["bool"]


def test_knn_query_scales_candidate_pool_with_k():
    q = knn_query([0.1, 0.2, 0.3], k=10)

    assert q["field"] == "embedding"
    assert q["query_vector"] == [0.1, 0.2, 0.3]
    assert q["k"] == 10
    assert q["num_candidates"] == 10 * KNN_CANDIDATE_MULTIPLIER


def test_knn_query_prefilters_with_the_same_clauses_as_bm25():
    knn = knn_query([0.1, 0.2, 0.3], k=10, filters=FILTERS)
    bm25 = bm25_query("vector search", FILTERS)

    # both halves of hybrid search must see the identical subset, or fusion
    # merges two differently-scoped result sets
    assert knn["filter"]["bool"]["filter"] == bm25["bool"]["filter"]


def test_knn_query_omits_filter_key_when_unfiltered():
    assert "filter" not in knn_query([0.1, 0.2, 0.3], k=10)


def test_highlight_config_targets_content():
    fields = highlight_config()["fields"]

    assert fields["content"]["type"] == "unified"
    assert fields["content"]["number_of_fragments"] >= 1


def test_facet_aggs_covers_three_aggregation_shapes():
    aggs = facet_aggs()

    assert set(aggs) == {"categories", "tags", "by_month", "word_count"}
    assert "terms" in aggs["categories"]
    assert "terms" in aggs["tags"]
    assert aggs["by_month"]["date_histogram"]["calendar_interval"] == "month"
    assert aggs["word_count"]["stats"]["field"] == "word_count"


def test_recency_boosted_query_decays_on_published():
    fn = recency_boosted_query("vector search")["function_score"]

    assert "bool" in fn["query"]  # wraps the normal text query
    assert fn["functions"][0]["gauss"]["published"]["decay"] == 0.5
    assert fn["boost_mode"] == "multiply"


def test_rrf_rank_constant_matches_the_paper():
    assert RRF_RANK_CONSTANT == 60
