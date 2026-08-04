from unittest.mock import patch

import httpx
from openai import AuthenticationError, NotFoundError
from fastapi.testclient import TestClient

from hybrid_search_api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("hybrid_search_api.api.routes.embed")
@patch("hybrid_search_api.api.routes.hybrid_search")
@patch("hybrid_search_api.api.routes.build_client")
def test_search_without_llm_answer(mock_build_client, mock_hybrid_search, mock_embed):
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_hybrid_search.return_value = [
        {"_id": "1", "_score": 1.0, "_source": {"title": "T", "content": "C"}}
    ]
    response = client.post("/search", json={"query": "test", "use_llm_answer": False})
    assert response.status_code == 200
    body = response.json()
    assert body["hits"][0]["title"] == "T"
    assert body["answer"] is None


@patch("hybrid_search_api.api.routes.LLMClient")
@patch("hybrid_search_api.api.routes.embed")
@patch("hybrid_search_api.api.routes.hybrid_search")
@patch("hybrid_search_api.api.routes.build_client")
def test_search_returns_502_on_bad_api_key(
    mock_build_client, mock_hybrid_search, mock_embed, mock_llm_cls
):
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_hybrid_search.return_value = [
        {"_id": "1", "_score": 1.0, "_source": {"title": "T", "content": "C"}}
    ]
    fake_response = httpx.Response(401, request=httpx.Request("POST", "https://llm.example.com"))
    mock_llm_cls.return_value.complete.side_effect = AuthenticationError(
        message="invalid x-api-key", response=fake_response, body=None
    )

    response = client.post("/search", json={"query": "test", "use_llm_answer": True})

    assert response.status_code == 502
    assert "API-Key" in response.json()["detail"]


@patch("hybrid_search_api.api.routes.LLMClient")
@patch("hybrid_search_api.api.routes.embed")
@patch("hybrid_search_api.api.routes.hybrid_search")
@patch("hybrid_search_api.api.routes.build_client")
def test_search_returns_502_on_unknown_model(
    mock_build_client, mock_hybrid_search, mock_embed, mock_llm_cls
):
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_hybrid_search.return_value = [
        {"_id": "1", "_score": 1.0, "_source": {"title": "T", "content": "C"}}
    ]
    fake_response = httpx.Response(404, request=httpx.Request("POST", "https://llm.example.com"))
    mock_llm_cls.return_value.complete.side_effect = NotFoundError(
        message="model not found", response=fake_response, body=None
    )

    response = client.post("/search", json={"query": "test", "use_llm_answer": True})

    assert response.status_code == 502
    assert "Modell" in response.json()["detail"]

