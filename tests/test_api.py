from unittest.mock import patch

from fastapi.testclient import TestClient

from hybrid_search_api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("hybrid_search_api.api.routes.hybrid_search")
@patch("hybrid_search_api.api.routes.build_client")
def test_search_without_llm_answer(mock_build_client, mock_hybrid_search):
    mock_hybrid_search.return_value = [
        {"_id": "1", "_score": 1.0, "_source": {"title": "T", "content": "C"}}
    ]
    response = client.post("/search", json={"query": "test", "use_llm_answer": False})
    assert response.status_code == 200
    body = response.json()
    assert body["hits"][0]["title"] == "T"
    assert body["answer"] is None
