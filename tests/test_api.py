from unittest.mock import patch

import httpx
from elasticsearch import ConnectionError as ESConnectionError
from fastapi.testclient import TestClient
from openai import APIConnectionError, AuthenticationError, NotFoundError, RateLimitError

from hybrid_search_api.main import app
from hybrid_search_api.models import SearchHit, SearchResponse

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("hybrid_search_api.api.routes.answer_search")
def test_search_returns_200_with_hits(mock_answer_search):
    mock_answer_search.return_value = SearchResponse(
        query="test", hits=[SearchHit(id="1", score=1.0, title="T", content="C")], answer=None
    )

    response = client.post("/search", json={"query": "test", "use_llm_answer": False})

    assert response.status_code == 200
    body = response.json()
    assert body["hits"][0]["title"] == "T"
    assert body["answer"] is None


@patch("hybrid_search_api.api.routes.answer_search")
def test_search_returns_502_on_bad_api_key(mock_answer_search):
    fake_response = httpx.Response(401, request=httpx.Request("POST", "https://llm.example.com"))
    mock_answer_search.side_effect = AuthenticationError(
        message="invalid x-api-key", response=fake_response, body=None
    )

    response = client.post("/search", json={"query": "test", "use_llm_answer": True})

    assert response.status_code == 502
    assert "API key" in response.json()["detail"]


@patch("hybrid_search_api.api.routes.answer_search")
def test_search_returns_german_error_when_lang_de(mock_answer_search):
    fake_response = httpx.Response(401, request=httpx.Request("POST", "https://llm.example.com"))
    mock_answer_search.side_effect = AuthenticationError(
        message="invalid x-api-key", response=fake_response, body=None
    )

    response = client.post(
        "/search", json={"query": "test", "use_llm_answer": True, "lang": "de"}
    )

    assert response.status_code == 502
    assert "API-Key" in response.json()["detail"]


@patch("hybrid_search_api.api.routes.answer_search")
def test_search_returns_502_on_unknown_model(mock_answer_search):
    fake_response = httpx.Response(404, request=httpx.Request("POST", "https://llm.example.com"))
    mock_answer_search.side_effect = NotFoundError(
        message="model not found", response=fake_response, body=None
    )

    response = client.post("/search", json={"query": "test", "use_llm_answer": True})

    assert response.status_code == 502
    assert "Model" in response.json()["detail"]


@patch("hybrid_search_api.api.routes.answer_search")
def test_search_returns_502_on_rate_limit(mock_answer_search):
    fake_response = httpx.Response(429, request=httpx.Request("POST", "https://llm.example.com"))
    mock_answer_search.side_effect = RateLimitError(
        message="rate limit exceeded", response=fake_response, body=None
    )

    response = client.post("/search", json={"query": "test", "use_llm_answer": True})

    assert response.status_code == 502
    assert "429" in response.json()["detail"]


@patch("hybrid_search_api.api.routes.answer_search")
def test_search_returns_502_on_connection_error(mock_answer_search):
    fake_request = httpx.Request("POST", "https://llm.example.com")
    mock_answer_search.side_effect = APIConnectionError(request=fake_request)

    response = client.post("/search", json={"query": "test", "use_llm_answer": True})

    assert response.status_code == 502
    assert "not reachable" in response.json()["detail"]


@patch("hybrid_search_api.api.routes.answer_search")
def test_search_returns_502_when_elasticsearch_unreachable(mock_answer_search):
    # Regression check: the global ES-connection-error handler in main.py covers
    # /search too, not just the introspection endpoints - previously this would
    # have bubbled up as a bare 500.
    mock_answer_search.side_effect = ESConnectionError("connection refused")

    response = client.post("/search", json={"query": "test", "use_llm_answer": False})

    assert response.status_code == 502
