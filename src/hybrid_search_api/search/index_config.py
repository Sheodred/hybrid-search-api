"""Elasticsearch index configuration: analyzers, filters, and field mappings.

This is the single place to adjust *how* documents are indexed and matched -
tokenization, stemming, stopwords, boosts, and the embedding field's
dimensionality. Query-time phrasing (how a search request itself looks)
lives separately in queries.py; this file only covers index-time settings.

To target a different language: swap "light_german" for another built-in
stemmer language (Elasticsearch ships one for most major languages, e.g.
"light_english") and "_german_" for the matching built-in stopword list,
e.g. "_english_".

To add domain-specific synonyms (e.g. "kNN" <-> "Vektorsuche"), add a
synonym filter to ANALYSIS_SETTINGS["filter"] and reference it in the
analyzer's filter chain below:

    "domain_synonyms": {
        "type": "synonym",
        "synonyms": ["knn, k-nearest-neighbor, vektorsuche"],
    }

A rendered copy of build_index_body()'s output lives in
docs/search/index_settings.json, kept in sync by
tests/test_config_snapshots.py - read it there instead of tracing the dicts.
"""

EMBEDDING_DIMS = 384  # must match the model in search/embeddings.py

ANALYSIS_SETTINGS = {
    "filter": {
        "de_stop": {
            "type": "stop",
            "stopwords": "_german_",
        },
        "de_stemmer": {
            "type": "stemmer",
            "language": "light_german",
        },
    },
    "analyzer": {
        "de_search_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "german_normalization", "de_stop", "de_stemmer"],
        }
    },
}

INDEX_MAPPING = {
    "properties": {
        "title": {
            "type": "text",
            "analyzer": "de_search_analyzer",
            # unanalyzed sub-field for exact matches, sorting, or aggregations
            "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
        },
        "content": {
            "type": "text",
            "analyzer": "de_search_analyzer",
        },
        "embedding": {
            "type": "dense_vector",
            "dims": EMBEDDING_DIMS,
            # "index": true is the 9.x default and therefore omitted. "similarity"
            # also defaults to cosine, but stays explicit - it decides how vectors
            # are compared, which is worth reading off the mapping directly.
            "similarity": "cosine",
        },
    }
}


def build_index_body() -> dict:
    """Full index creation body: analysis settings + field mappings."""
    return {"settings": {"analysis": ANALYSIS_SETTINGS}, "mappings": INDEX_MAPPING}
