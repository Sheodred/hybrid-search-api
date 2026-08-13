from unittest.mock import patch

import httpx
import pytest
from openai import APIConnectionError, AuthenticationError, NotFoundError, RateLimitError

from hybrid_search_api.config import Settings
from hybrid_search_api.models import SearchRequest
from hybrid_search_api.search.answering import answer_search

_RAW_HIT = {"_id": "1", "_score": 1.0, "_source": {"title": "T", "content": "C"}}


class _FakeLLMClient:
    def __init__(self, *, answer=None, error=None):
        self._answer = answer
        self._error = error

    def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        if self._error is not None:
            raise self._error
        return self._answer


@patch("hybrid_search_api.search.answering.hybrid_search")
@patch("hybrid_search_api.search.answering.embed")
@patch("hybrid_search_api.search.answering.build_client")
def test_answer_search_prefers_rrf_score_over_original_score(
    mock_build_client, mock_embed, mock_hybrid_search
):
    # After RRF fusion, a hit dict carries both the original per-list _score
    # (BM25 or kNN) and the fused _rrf_score used to rank it. The fused score
    # is what the ranking is actually sorted by, so it's the one that should
    # be displayed - not the leftover original.
    fused_hit = {
        "_id": "1",
        "_score": 12.5,
        "_rrf_score": 0.031,
        "_source": {"title": "T", "content": "C"},
    }
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_hybrid_search.return_value = [fused_hit]

    response = answer_search(
        SearchRequest(query="test", use_llm_answer=False), Settings()
    )

    assert response.hits[0].score == 0.031


@patch("hybrid_search_api.search.answering.hybrid_search")
@patch("hybrid_search_api.search.answering.embed")
@patch("hybrid_search_api.search.answering.build_client")
def test_answer_search_without_llm_answer(mock_build_client, mock_embed, mock_hybrid_search):
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_hybrid_search.return_value = [_RAW_HIT]

    response = answer_search(
        SearchRequest(query="test", use_llm_answer=False), Settings()
    )

    assert response.hits[0].title == "T"
    assert response.answer is None


@patch("hybrid_search_api.search.answering.hybrid_search")
@patch("hybrid_search_api.search.answering.embed")
@patch("hybrid_search_api.search.answering.build_client")
def test_answer_search_returns_llm_answer_when_requested(
    mock_build_client, mock_embed, mock_hybrid_search
):
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_hybrid_search.return_value = [_RAW_HIT]
    fake_llm = _FakeLLMClient(answer="Here is the answer.")

    response = answer_search(
        SearchRequest(query="test", use_llm_answer=True), Settings(), llm_client=fake_llm
    )

    assert response.answer == "Here is the answer."


@patch("hybrid_search_api.search.answering.hybrid_search")
@patch("hybrid_search_api.search.answering.embed")
@patch("hybrid_search_api.search.answering.build_client")
def test_answer_search_propagates_authentication_error(
    mock_build_client, mock_embed, mock_hybrid_search
):
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_hybrid_search.return_value = [_RAW_HIT]
    fake_response = httpx.Response(401, request=httpx.Request("POST", "https://llm.example.com"))
    fake_llm = _FakeLLMClient(
        error=AuthenticationError(message="invalid x-api-key", response=fake_response, body=None)
    )

    with pytest.raises(AuthenticationError):
        answer_search(
            SearchRequest(query="test", use_llm_answer=True), Settings(), llm_client=fake_llm
        )


@patch("hybrid_search_api.search.answering.hybrid_search")
@patch("hybrid_search_api.search.answering.embed")
@patch("hybrid_search_api.search.answering.build_client")
def test_answer_search_propagates_not_found_error(
    mock_build_client, mock_embed, mock_hybrid_search
):
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_hybrid_search.return_value = [_RAW_HIT]
    fake_response = httpx.Response(404, request=httpx.Request("POST", "https://llm.example.com"))
    fake_llm = _FakeLLMClient(
        error=NotFoundError(message="model not found", response=fake_response, body=None)
    )

    with pytest.raises(NotFoundError):
        answer_search(
            SearchRequest(query="test", use_llm_answer=True), Settings(), llm_client=fake_llm
        )


@patch("hybrid_search_api.search.answering.hybrid_search")
@patch("hybrid_search_api.search.answering.embed")
@patch("hybrid_search_api.search.answering.build_client")
def test_answer_search_propagates_rate_limit_error(
    mock_build_client, mock_embed, mock_hybrid_search
):
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_hybrid_search.return_value = [_RAW_HIT]
    fake_response = httpx.Response(429, request=httpx.Request("POST", "https://llm.example.com"))
    fake_llm = _FakeLLMClient(
        error=RateLimitError(message="rate limit exceeded", response=fake_response, body=None)
    )

    with pytest.raises(RateLimitError):
        answer_search(
            SearchRequest(query="test", use_llm_answer=True), Settings(), llm_client=fake_llm
        )


@patch("hybrid_search_api.search.answering.hybrid_search")
@patch("hybrid_search_api.search.answering.embed")
@patch("hybrid_search_api.search.answering.build_client")
def test_answer_search_propagates_connection_error(
    mock_build_client, mock_embed, mock_hybrid_search
):
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_hybrid_search.return_value = [_RAW_HIT]
    fake_request = httpx.Request("POST", "https://llm.example.com")
    fake_llm = _FakeLLMClient(error=APIConnectionError(request=fake_request))

    with pytest.raises(APIConnectionError):
        answer_search(
            SearchRequest(query="test", use_llm_answer=True), Settings(), llm_client=fake_llm
        )


@patch("hybrid_search_api.search.answering.hybrid_search")
@patch("hybrid_search_api.search.answering.embed")
@patch("hybrid_search_api.search.answering.build_client")
def test_answer_search_falls_back_to_bm25_when_embedding_fails(
    mock_build_client, mock_embed, mock_hybrid_search
):
    mock_embed.side_effect = RuntimeError("model unavailable")
    mock_hybrid_search.return_value = [_RAW_HIT]

    answer_search(SearchRequest(query="test", use_llm_answer=False), Settings())

    _, kwargs = mock_hybrid_search.call_args
    assert kwargs["query_vector"] is None
