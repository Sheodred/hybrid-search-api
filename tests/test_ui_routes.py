from fastapi.testclient import TestClient

from hybrid_search_api.main import app

client = TestClient(app)


def test_root_serves_search_ui_html():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>" in response.text
