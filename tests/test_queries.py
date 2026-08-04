from hybrid_search_api.search.queries import bm25_query, knn_query


def test_bm25_query_boosts_title_and_allows_typos():
    q = bm25_query("Vektorsuche")

    assert q["multi_match"]["query"] == "Vektorsuche"
    assert q["multi_match"]["fields"] == ["title^2", "content"]
    assert q["multi_match"]["fuzziness"] == "AUTO"


def test_knn_query_scales_candidate_pool_with_k():
    q = knn_query([0.1, 0.2, 0.3], k=10)

    assert q["field"] == "embedding"
    assert q["query_vector"] == [0.1, 0.2, 0.3]
    assert q["k"] == 10
    assert q["num_candidates"] == 50  # 10 * KNN_CANDIDATE_MULTIPLIER (5)
