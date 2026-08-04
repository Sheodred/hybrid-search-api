from hybrid_search_api.search.index_config import build_index_body


def test_build_index_body_has_settings_and_mappings():
    body = build_index_body()

    assert "settings" in body
    assert "mappings" in body
    assert body["mappings"]["properties"]["embedding"]["dims"] == 384
    assert body["mappings"]["properties"]["title"]["analyzer"] == "de_search_analyzer"
    assert "de_search_analyzer" in body["settings"]["analysis"]["analyzer"]
