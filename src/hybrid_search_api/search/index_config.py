"""Elasticsearch index configuration: analyzers, filters, and field mappings.

This is the single place to adjust *how* documents are indexed and matched -
tokenization, stemming, stopwords, synonyms, and the embedding field's
dimensionality. Query-time phrasing (how a search request itself looks)
lives separately in queries.py; this file only covers index-time settings.

The mapping is deliberately broader than a minimal search service needs -
it is meant to be read. See docs/search/README.md for what each piece
demonstrates and docs/adr/0004-rich-index-and-query-showcase.md for why.

Two ideas drive the analysis chain:

1. **Index/search analyzer split.** Documents are indexed with `en_index`;
   queries are analyzed with `en_search`, which is the same chain plus
   synonym expansion. Expanding at search time keeps the index small and
   lets the synonym list change without a full reindex (an analyzer reload
   is still required).
2. **Multi-fields.** `title` and `content` each carry an `exact` sub-field
   analyzed without stemming or stopword removal, so phrase queries can
   match the literal wording that the stemmed main field has thrown away.

To target a different language: swap "light_english" for another built-in
stemmer language (Elasticsearch ships one for most major languages, e.g.
"light_german") and "_english_" for the matching built-in stopword list,
e.g. "_german_", and drop "en_possessive" (it is English-specific).

A rendered copy of build_index_body()'s output lives in
docs/search/index_settings.json, kept in sync by
tests/test_config_snapshots.py - read it there instead of tracing the dicts.
"""

EMBEDDING_DIMS = 384  # must match the model in search/embeddings.py

# Domain vocabulary this corpus talks about, where a user's phrasing and the
# documents' phrasing routinely differ ("knn" vs "nearest neighbor"). Applied
# search-side only. synonym_graph (not synonym) is what handles the
# multi-word entries correctly.
DOMAIN_SYNONYMS = [
    "knn, k nearest neighbor, k-nearest-neighbor, ann, approximate nearest neighbor",
    "rag, retrieval augmented generation, retrieval-augmented generation",
    "bm25, okapi bm25, best match 25",
    "vector search, semantic search, dense retrieval, embedding search",
    "hnsw, hierarchical navigable small world",
    "nlp, natural language processing",
]

ANALYSIS_SETTINGS = {
    "filter": {
        "en_stop": {
            "type": "stop",
            "stopwords": "_english_",
        },
        "en_stemmer": {
            "type": "stemmer",
            "language": "light_english",
        },
        "en_possessive": {
            "type": "stemmer",
            "language": "possessive_english",
        },
        "domain_synonyms": {
            "type": "synonym_graph",
            "synonyms": DOMAIN_SYNONYMS,
        },
    },
    "analyzer": {
        # Index-time: no synonym expansion (see module docstring).
        "en_index": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "en_possessive", "en_stop", "en_stemmer", "asciifolding"],
        },
        # Search-time: same chain, plus synonyms. Placed after lowercase /
        # possessive-stripping and before stopwords / stemming so expansions
        # get stopworded and stemmed exactly like the indexed terms.
        "en_search": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
                "lowercase",
                "en_possessive",
                "domain_synonyms",
                "en_stop",
                "en_stemmer",
                "asciifolding",
            ],
        },
        # Deliberately minimal: keeps the literal wording, so match_phrase on
        # an .exact sub-field means what it says.
        "exact": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "asciifolding"],
        },
    },
    "normalizer": {
        # keyword fields aren't analyzed, so case-folding needs a normalizer:
        # "Vector-Search" and "vector-search" become one aggregation bucket.
        "keyword_lower": {
            "type": "custom",
            "filter": ["lowercase", "asciifolding"],
        }
    },
}

INDEX_MAPPING = {
    # Reject documents carrying fields this mapping doesn't declare, instead of
    # silently inventing a type for them. A seed script that adds a field has
    # to declare it here first - typos fail loudly at index time.
    "dynamic": "strict",
    "properties": {
        "title": {
            "type": "text",
            "analyzer": "en_index",
            "search_analyzer": "en_search",
            "copy_to": "all_text",
            "fields": {
                # unanalyzed sub-field for exact matches, sorting, or aggregations
                "keyword": {"type": "keyword", "ignore_above": 256},
                # unstemmed sub-field for phrase matching
                "exact": {"type": "text", "analyzer": "exact"},
            },
        },
        "content": {
            "type": "text",
            "analyzer": "en_index",
            "search_analyzer": "en_search",
            "copy_to": "all_text",
            # Stores positions and offsets so the unified highlighter can cut
            # accurate snippets without re-analyzing the field at query time.
            "term_vector": "with_positions_offsets",
            "fields": {
                "exact": {"type": "text", "analyzer": "exact"},
            },
        },
        # copy_to catch-all: one field that holds title + content + tags, so a
        # query can fall back to "match anywhere" without listing every field.
        "all_text": {
            "type": "text",
            "analyzer": "en_index",
            "search_analyzer": "en_search",
        },
        "embedding": {
            "type": "dense_vector",
            "dims": EMBEDDING_DIMS,
            # "index": true is the 9.x default and therefore omitted.
            "similarity": "cosine",
            # Explicit int8_hnsw: 4x smaller than raw float32 vectors at
            # essentially unchanged recall. Without this, 9.x picks bbq_hnsw
            # at 384 dims - stating it keeps the tuning knob visible and the
            # snapshot stable across versions.
            "index_options": {"type": "int8_hnsw", "m": 16, "ef_construction": 100},
        },
        "category": {"type": "keyword", "normalizer": "keyword_lower"},
        "tags": {"type": "keyword", "normalizer": "keyword_lower", "copy_to": "all_text"},
        "published": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
        "source": {"type": "keyword"},
        # Returned for citation/display, never searched - index: false saves
        # the inverted index for a field no query touches.
        "url": {"type": "keyword", "index": False},
        "word_count": {"type": "integer"},
    },
}


def build_index_body() -> dict:
    """Full index creation body: analysis settings + field mappings."""
    return {"settings": {"analysis": ANALYSIS_SETTINGS}, "mappings": INDEX_MAPPING}
