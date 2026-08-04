from unittest.mock import MagicMock

from hybrid_search_api.search.elasticsearch_client import ensure_index


def test_ensure_index_creates_when_missing():
    client = MagicMock()
    client.indices.exists.return_value = False

    ensure_index(client, "documents")

    client.indices.create.assert_called_once()
    _, kwargs = client.indices.create.call_args
    assert kwargs["index"] == "documents"
    assert "settings" in kwargs
    assert "mappings" in kwargs


def test_ensure_index_skips_when_already_present():
    client = MagicMock()
    client.indices.exists.return_value = True

    ensure_index(client, "documents")

    client.indices.create.assert_not_called()
