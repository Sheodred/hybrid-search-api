from unittest.mock import MagicMock, patch

from hybrid_search_api.search.embeddings import _get_model, embed, embed_many


@patch("hybrid_search_api.search.embeddings.SentenceTransformer")
def test_embed_returns_list_of_floats(mock_st_cls):
    _get_model.cache_clear()
    mock_model = MagicMock()
    mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
    mock_st_cls.return_value = mock_model

    result = embed("hallo welt")

    assert result == [0.1, 0.2, 0.3]


@patch("hybrid_search_api.search.embeddings.SentenceTransformer")
def test_embed_many_batches_multiple_texts(mock_st_cls):
    _get_model.cache_clear()
    mock_model = MagicMock()
    mock_model.encode.return_value = MagicMock(tolist=lambda: [[0.1, 0.2], [0.3, 0.4]])
    mock_st_cls.return_value = mock_model

    result = embed_many(["a", "b"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    mock_model.encode.assert_called_once_with(["a", "b"], normalize_embeddings=True)
