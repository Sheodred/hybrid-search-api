from unittest.mock import Mock

from hybrid_search_api.models import SearchFilters
from hybrid_search_api.search.hybrid_search import (
    _reciprocal_rank_fusion,
    hybrid_search,
)

AGGREGATIONS = {
    "categories": {"buckets": [{"key": "vector-search", "doc_count": 2}]},
    "tags": {"buckets": [{"key": "hnsw", "doc_count": 1}]},
    "by_month": {
        "buckets": [{"key": 1704067200000, "key_as_string": "2024-01-01", "doc_count": 2}]
    },
    "word_count": {"count": 2, "min": 40.0, "max": 80.0, "avg": 60.0},
}


def _hit(doc_id, score=1.0, highlight=None):
    hit = {"_id": doc_id, "_score": score, "_source": {"title": doc_id, "content": "c"}}
    if highlight:
        hit["highlight"] = {"content": highlight}
    return hit


def _response(hits, aggregations=None):
    resp = {"hits": {"hits": hits}}
    if aggregations is not None:
        resp["aggregations"] = aggregations
    return resp


def test_rrf_favors_docs_ranked_high_in_both_lists():
    bm25 = [{"_id": "a"}, {"_id": "b"}, {"_id": "c"}]
    knn = [{"_id": "b"}, {"_id": "a"}, {"_id": "d"}]

    fused = _reciprocal_rank_fusion(bm25, knn)
    fused_ids = [hit["_id"] for hit in fused]

    # "a" and "b" appear near the top of both lists, so they should lead the fused ranking
    assert fused_ids[0] in {"a", "b"}
    assert fused_ids[1] in {"a", "b"}
    assert "d" in fused_ids  # docs from either single list should still show up


def test_rrf_keeps_the_highlight_from_the_list_that_had_one():
    # Only the BM25 call requests highlights. A document found by both sides
    # must not lose its snippet when the kNN copy is merged in - and those are
    # exactly the documents RRF promotes to the top.
    bm25 = [_hit("a", highlight=["a <em>match</em>"])]
    knn = [_hit("a")]

    fused = _reciprocal_rank_fusion(bm25, knn)

    assert fused[0]["highlight"] == {"content": ["a <em>match</em>"]}


def test_bm25_only_when_no_vector_is_given():
    client = Mock()
    client.search.return_value = _response([_hit("a")], AGGREGATIONS)

    result = hybrid_search(client, "documents", "vector search")

    assert client.search.call_count == 1
    assert "query" in client.search.call_args.kwargs
    assert [h["_id"] for h in result.hits] == ["a"]


def test_vector_path_runs_both_queries_and_fuses():
    client = Mock()
    client.search.side_effect = [
        _response([_hit("a"), _hit("b")], AGGREGATIONS),
        _response([_hit("b"), _hit("c")]),
    ]

    result = hybrid_search(client, "documents", "vector search", query_vector=[0.1, 0.2])

    assert client.search.call_count == 2
    assert "query" in client.search.call_args_list[0].kwargs
    assert "knn" in client.search.call_args_list[1].kwargs
    # "b" is in both lists, so it leads the fused ranking
    assert [h["_id"] for h in result.hits][0] == "b"
    assert all("_rrf_score" in h for h in result.hits)


def test_embedding_is_never_returned_in_the_source():
    client = Mock()
    client.search.side_effect = [
        _response([_hit("a")], AGGREGATIONS),
        _response([_hit("a")]),
    ]

    hybrid_search(client, "documents", "q", query_vector=[0.1])

    for call in client.search.call_args_list:
        assert call.kwargs["source_excludes"] == ["embedding"]


def test_filters_reach_both_sides_of_the_search():
    client = Mock()
    client.search.side_effect = [
        _response([_hit("a")], AGGREGATIONS),
        _response([_hit("a")]),
    ]
    filters = SearchFilters(category=["vector-search"])

    hybrid_search(client, "documents", "q", query_vector=[0.1], filters=filters)

    bm25_kwargs, knn_kwargs = (c.kwargs for c in client.search.call_args_list)
    expected = [{"terms": {"category": ["vector-search"]}}]
    assert bm25_kwargs["query"]["bool"]["filter"] == expected
    assert knn_kwargs["knn"]["filter"]["bool"]["filter"] == expected


def test_aggregations_are_parsed_into_facets_and_stats():
    client = Mock()
    client.search.return_value = _response([_hit("a")], AGGREGATIONS)

    result = hybrid_search(client, "documents", "q")

    assert [b.key for b in result.facets["categories"]] == ["vector-search"]
    assert result.facets["categories"][0].doc_count == 2
    # date_histogram buckets surface the readable key, not epoch millis
    assert result.facets["by_month"][0].key == "2024-01-01"
    # the stats agg is not a facet - it has its own field
    assert "word_count" not in result.facets
    assert result.word_count_stats.avg == 60.0
    assert result.word_count_stats.count == 2


def test_missing_aggregations_are_tolerated():
    client = Mock()
    client.search.return_value = _response([_hit("a")])

    result = hybrid_search(client, "documents", "q")

    assert result.facets is None
    assert result.word_count_stats is None


def test_highlights_survive_all_the_way_through_hybrid_search():
    client = Mock()
    client.search.side_effect = [
        _response([_hit("a", highlight=["<em>vector</em> search"])], AGGREGATIONS),
        _response([_hit("a")]),
    ]

    result = hybrid_search(client, "documents", "q", query_vector=[0.1])

    assert result.hits[0]["highlight"]["content"] == ["<em>vector</em> search"]
