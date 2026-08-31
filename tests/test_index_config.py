from hybrid_search_api.search.index_config import EMBEDDING_DIMS, build_index_body


def test_build_index_body_has_settings_and_mappings():
    body = build_index_body()

    assert "settings" in body
    assert "mappings" in body
    assert body["mappings"]["properties"]["embedding"]["dims"] == EMBEDDING_DIMS


def test_index_and_search_analyzers_are_split():
    # The whole point of the split: documents are indexed without synonym
    # expansion, queries are analyzed with it.
    props = build_index_body()["mappings"]["properties"]

    for field in ("title", "content"):
        assert props[field]["analyzer"] == "en_index"
        assert props[field]["search_analyzer"] == "en_search"
        assert props[field]["analyzer"] != props[field]["search_analyzer"]


def test_synonyms_are_search_time_only():
    analyzers = build_index_body()["settings"]["analysis"]["analyzer"]

    assert "domain_synonyms" in analyzers["en_search"]["filter"]
    assert "domain_synonyms" not in analyzers["en_index"]["filter"]
    # synonym_graph, not synonym - the multi-word entries need the graph form
    filters = build_index_body()["settings"]["analysis"]["filter"]
    assert filters["domain_synonyms"]["type"] == "synonym_graph"


def test_exact_subfields_skip_stemming():
    props = build_index_body()["mappings"]["properties"]

    assert props["title"]["fields"]["exact"]["analyzer"] == "exact"
    assert props["content"]["fields"]["exact"]["analyzer"] == "exact"
    exact_chain = build_index_body()["settings"]["analysis"]["analyzer"]["exact"]["filter"]
    assert "en_stemmer" not in exact_chain
    assert "en_stop" not in exact_chain


def test_mapping_is_strict_so_unknown_fields_are_rejected():
    assert build_index_body()["mappings"]["dynamic"] == "strict"


def test_embedding_is_quantized_explicitly():
    # Without explicit index_options, ES 9.x picks bbq_hnsw at 384 dims.
    embedding = build_index_body()["mappings"]["properties"]["embedding"]

    assert embedding["index_options"]["type"] == "int8_hnsw"
    assert embedding["similarity"] == "cosine"


def test_url_is_stored_but_not_searchable():
    assert build_index_body()["mappings"]["properties"]["url"]["index"] is False


def test_copy_to_catch_all_is_wired():
    props = build_index_body()["mappings"]["properties"]

    assert props["title"]["copy_to"] == "all_text"
    assert props["content"]["copy_to"] == "all_text"
    assert props["tags"]["copy_to"] == "all_text"
    assert props["all_text"]["type"] == "text"


def test_keyword_facet_fields_are_case_normalized():
    props = build_index_body()["mappings"]["properties"]

    assert props["category"]["normalizer"] == "keyword_lower"
    assert props["tags"]["normalizer"] == "keyword_lower"


def test_content_stores_term_vectors_for_highlighting():
    props = build_index_body()["mappings"]["properties"]

    assert props["content"]["term_vector"] == "with_positions_offsets"
