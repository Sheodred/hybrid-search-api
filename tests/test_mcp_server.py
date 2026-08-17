from unittest.mock import patch

from hybrid_search_api.mcp_server import search

_RAW_HIT = {"_id": "1", "_score": 1.0, "_source": {"title": "T", "content": "C"}}


@patch("hybrid_search_api.search.answering.answer_search")
def test_search_tool_builds_request_and_returns_dict(mock_answer_search):
    from hybrid_search_api.models import SearchHit, SearchResponse

    mock_answer_search.return_value = SearchResponse(
        query="test", hits=[SearchHit(id="1", score=1.0, title="T", content="C")], answer="A"
    )

    result = search(query="test", top_k=3, use_llm_answer=True, lang="de")

    request = mock_answer_search.call_args[0][0]
    assert request.query == "test"
    assert request.top_k == 3
    assert request.use_llm_answer is True
    assert request.lang == "de"
    assert result == {
        "query": "test",
        "hits": [{"id": "1", "score": 1.0, "title": "T", "content": "C"}],
        "answer": "A",
    }
