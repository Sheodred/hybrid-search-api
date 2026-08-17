import json
from types import SimpleNamespace
from unittest.mock import patch

from hybrid_search_api.config import Settings
from hybrid_search_api.models import SearchHit, SearchRequest, SearchResponse
from hybrid_search_api.search.agentic_answering import agentic_answer_search


def _tool_call(call_id: str, name: str, arguments: dict) -> SimpleNamespace:
    return SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


def _message(content: str | None = None, tool_calls: list | None = None) -> SimpleNamespace:
    return SimpleNamespace(content=content, tool_calls=tool_calls or [])


class _ScriptedLLMClient:
    def __init__(self, responses: list[SimpleNamespace]):
        self._responses = list(responses)

    def complete_with_tools(self, messages, tools, max_tokens=1024):
        return self._responses.pop(0)


@patch("hybrid_search_api.search.answering.answer_search")
def test_agentic_loop_calls_search_then_answers(mock_answer_search):
    mock_answer_search.return_value = SearchResponse(
        query="test", hits=[SearchHit(id="1", score=1.0, title="T", content="C")], answer=None
    )
    llm = _ScriptedLLMClient(
        [
            _message(tool_calls=[_tool_call("call1", "search", {"query": "test", "use_llm_answer": False})]),
            _message(content="Final answer."),
        ]
    )

    response = agentic_answer_search(SearchRequest(query="test", agentic=True), Settings(), llm_client=llm)

    assert response.answer == "Final answer."
    assert response.hits[0].title == "T"


@patch("hybrid_search_api.search.answering.answer_search")
def test_agentic_loop_answers_without_calling_tool(mock_answer_search):
    llm = _ScriptedLLMClient([_message(content="I already know this.")])

    response = agentic_answer_search(SearchRequest(query="test", agentic=True), Settings(), llm_client=llm)

    assert response.answer == "I already know this."
    assert response.hits == []
    mock_answer_search.assert_not_called()


@patch("hybrid_search_api.search.answering.answer_search")
def test_agentic_loop_forces_final_answer_after_round_cap(mock_answer_search):
    mock_answer_search.return_value = SearchResponse(
        query="test", hits=[SearchHit(id="1", score=1.0, title="T", content="C")], answer=None
    )
    tool_call_message = _message(tool_calls=[_tool_call("call1", "search", {"query": "test", "use_llm_answer": False})])
    llm = _ScriptedLLMClient(
        [tool_call_message, tool_call_message, tool_call_message, _message(content="Forced answer.")]
    )

    response = agentic_answer_search(SearchRequest(query="test", agentic=True), Settings(), llm_client=llm)

    assert response.answer == "Forced answer."
