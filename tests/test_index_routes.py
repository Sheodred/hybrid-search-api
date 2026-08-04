from unittest.mock import MagicMock, patch

from elasticsearch import ConnectionError as ESConnectionError
from fastapi.testclient import TestClient

from hybrid_search_api.main import app

client = TestClient(app)


@patch("hybrid_search_api.api.index_routes.build_client")
def test_elasticsearch_health(mock_build_client):
    mock_es = MagicMock()
    mock_es.cluster.health.return_value = {
        "status": "green",
        "cluster_name": "docker-cluster",
        "number_of_nodes": 1,
        "active_shards": 3,
        "unassigned_shards": 0,
    }
    mock_build_client.return_value = mock_es

    response = client.get("/health/elasticsearch")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "green"
    assert body["number_of_nodes"] == 1


@patch("hybrid_search_api.api.index_routes.build_client")
def test_elasticsearch_health_returns_502_when_unreachable(mock_build_client):
    mock_es = MagicMock()
    mock_es.cluster.health.side_effect = ESConnectionError("connection refused")
    mock_build_client.return_value = mock_es

    response = client.get("/health/elasticsearch")

    assert response.status_code == 502
    assert "Elasticsearch" in response.json()["detail"]


@patch("hybrid_search_api.api.index_routes.build_client")
def test_index_info_when_missing(mock_build_client):
    mock_es = MagicMock()
    mock_es.indices.exists.return_value = False
    mock_build_client.return_value = mock_es

    response = client.get("/index")

    assert response.status_code == 200
    body = response.json()
    assert body["exists"] is False
    assert body["document_count"] is None


@patch("hybrid_search_api.api.index_routes.build_client")
def test_index_info_when_present(mock_build_client):
    mock_es = MagicMock()
    mock_es.indices.exists.return_value = True
    mock_es.count.return_value = {"count": 10}
    mock_es.indices.get_mapping.return_value = {
        "documents": {"mappings": {"properties": {"title": {"type": "text"}}}}
    }
    mock_build_client.return_value = mock_es

    response = client.get("/index")

    assert response.status_code == 200
    body = response.json()
    assert body["exists"] is True
    assert body["document_count"] == 10


@patch("hybrid_search_api.api.index_routes.build_client")
def test_list_documents_excludes_embedding_field(mock_build_client):
    mock_es = MagicMock()
    mock_es.search.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {"_id": "1", "_source": {"title": "T", "content": "C", "embedding": [0.1, 0.2]}}
            ],
        }
    }
    mock_build_client.return_value = mock_es

    response = client.get("/index/documents?limit=5&offset=0")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["documents"][0]["title"] == "T"
    assert "embedding" not in body["documents"][0]
