"""Utility script: indexes a small set of sample documents into Elasticsearch,
including their embeddings, so the API has something to search against
(BM25 and kNN) right after setup.

Usage:
    python scripts/seed_data.py
"""

from hybrid_search_api.config import get_settings
from hybrid_search_api.search.elasticsearch_client import build_client, ensure_index
from hybrid_search_api.search.embeddings import embed_many

SAMPLE_DOCS = [
    {
        "title": "Elasticsearch Basics",
        "content": (
            "Elasticsearch ist eine verteilte Such- und Analyse-Engine auf Basis von "
            "Apache Lucene."
        ),
    },
    {
        "title": "Vector Search",
        "content": (
            "kNN-Suche findet semantisch aehnliche Dokumente ueber Embedding-Vektoren "
            "statt exakter Wortuebereinstimmung."
        ),
    },
    {
        "title": "Retrieval-Augmented Generation",
        "content": (
            "RAG kombiniert Suchergebnisse mit einem LLM, um Antworten auf Basis "
            "konkreter Quellen zu generieren."
        ),
    },
]


def main() -> None:
    settings = get_settings()
    client = build_client(settings)
    ensure_index(client, settings.elasticsearch_index)

    print("Computing embeddings (first run downloads the model, ~80MB)...")
    vectors = embed_many([doc["content"] for doc in SAMPLE_DOCS])

    for i, (doc, vector) in enumerate(zip(SAMPLE_DOCS, vectors, strict=True), start=1):
        client.index(
            index=settings.elasticsearch_index,
            id=str(i),
            document={**doc, "embedding": vector},
        )
    client.indices.refresh(index=settings.elasticsearch_index)
    print(
        f"Indexed {len(SAMPLE_DOCS)} sample documents (with embeddings) "
        f"into '{settings.elasticsearch_index}'."
    )


if __name__ == "__main__":
    main()
