from hybrid_search_api.search.hybrid_search import _reciprocal_rank_fusion


def test_rrf_favors_docs_ranked_high_in_both_lists():
    bm25 = [{"_id": "a"}, {"_id": "b"}, {"_id": "c"}]
    knn = [{"_id": "b"}, {"_id": "a"}, {"_id": "d"}]

    fused = _reciprocal_rank_fusion(bm25, knn)
    fused_ids = [hit["_id"] for hit in fused]

    # "a" and "b" appear near the top of both lists, so they should lead the fused ranking
    assert fused_ids[0] in {"a", "b"}
    assert fused_ids[1] in {"a", "b"}
    assert "d" in fused_ids  # docs from either single list should still show up
