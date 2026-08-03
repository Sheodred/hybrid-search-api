"""Utility script: indexes a small set of sample documents into Elasticsearch
so the API has something to search against right after setup.

Note: samples are indexed without embeddings, so kNN search has nothing to
match yet - hybrid_search() falls back to BM25-only until an embedding model
is wired in (see README roadmap).

Usage:
    python scripts/seed_data.py
"""

from hybrid_search_api.config import get_settings
from hybrid_search_api.search.elasticsearch_client import build_client, ensure_index

SAMPLE_DOCS = [
    {
        "title": "Elasticsearch Basics",
        "content": "Elasticsearch ist eine verteilte Such- und Analyse-Engine auf Basis von Apache Lucene.",
    },
    {
        "title": "Vector Search",
        "content": "kNN-Suche findet semantisch aehnliche Dokumente ueber Embedding-Vektoren statt exakter Wortuebereinstimmung.",
    },
    {
        "title": "Retrieval-Augmented Generation",
        "content": "RAG kombiniert Suchergebnisse mit einem LLM, um Antworten auf Basis konkreter Quellen zu generieren.",
    },
]


def main() -> None:
    settings = get_settings()
    client = build_client(settings)
    ensure_index(client, settings.elasticsearch_index)
    for i, doc in enumerate(SAMPLE_DOCS, start=1):
        client.index(index=settings.elasticsearch_index, id=str(i), document=doc)
    client.indices.refresh(index=settings.elasticsearch_index)
    print(f"Indexed {len(SAMPLE_DOCS)} sample documents into '{settings.elasticsearch_index}'.")


if __name__ == "__main__":
    main()
