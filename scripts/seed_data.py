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
            "Elasticsearch is a distributed search and analytics engine built on top of "
            "Apache Lucene. It is suited for full-text search, structured search, and "
            "near-real-time analytics. Data is organized into indices, which are "
            "internally distributed across multiple shards."
        ),
    },
    {
        "title": "Vector Search and Embeddings",
        "content": (
            "Vector search represents text as high-dimensional numeric vectors "
            "(embeddings). Similar content lies close together in vector space, which "
            "means semantically related documents can be found even when there is no "
            "literal word match."
        ),
    },
    {
        "title": "Retrieval-Augmented Generation (RAG)",
        "content": (
            "RAG combines a search component with a language model: relevant documents "
            "are retrieved first, then the model generates an answer based on those "
            "sources. This reduces hallucinations and makes answers traceable."
        ),
    },
    {
        "title": "BM25 Ranking",
        "content": (
            "BM25 is a ranking function for classic full-text search that takes term "
            "frequency, inverse document frequency, and document length into account. "
            "It is the default scoring algorithm in Elasticsearch and delivers very good "
            "results for exact term matches."
        ),
    },
    {
        "title": "Reciprocal Rank Fusion (RRF)",
        "content": (
            "RRF fuses multiple ranked lists from different search methods without "
            "requiring their scores to be brought onto a common scale. Each document "
            "gets points based on its rank in every list, which makes RRF robust "
            "against outliers."
        ),
    },
    {
        "title": "Approximate Nearest Neighbor Search (HNSW)",
        "content": (
            "For kNN search, Elasticsearch uses the HNSW algorithm (Hierarchical "
            "Navigable Small World) to find similar vectors approximately but very "
            "quickly. The num_candidates parameter controls the balance between search "
            "speed and accuracy."
        ),
    },
    {
        "title": "Sentence Transformer Models",
        "content": (
            "Sentence transformer models like all-MiniLM-L6-v2 turn whole sentences "
            "into embedding vectors instead of considering individual words in "
            "isolation. This lets them capture context and meaning better than classic "
            "word embeddings."
        ),
    },
    {
        "title": "Full-Text Search vs. Semantic Search",
        "content": (
            "Full-text search finds documents through exact or fuzzy word matches, "
            "while semantic search relies on meaning similarity. Hybrid search combines "
            "both approaches to deliver precise term matches as well as content that is "
            "conceptually related."
        ),
    },
    {
        "title": "Analyzers and Tokenization",
        "content": (
            "An Elasticsearch analyzer breaks text into tokens and normalizes them, for "
            "example through lowercasing, stemming, or stopword removal. "
            "Language-specific analyzers, such as the German analyzer, noticeably "
            "improve match quality for German-language content."
        ),
    },
    {
        "title": "Prompt Engineering for RAG Systems",
        "content": (
            "How the system prompt is worded largely determines whether a RAG system "
            "answers strictly from the supplied sources or tends toward "
            "hallucinations. Clear instructions, explicit source references, and "
            "prompt versioning all improve traceability."
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
