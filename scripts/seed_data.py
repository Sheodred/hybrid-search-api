"""Utility script: indexes a small set of sample documents into Elasticsearch,
including their embeddings, so the API has something to search against
(BM25 and kNN) right after setup.

Each document carries hand-authored metadata (category, tags, published,
source, url) on top of title/content, so the filter and facet features in
search/queries.py have something real to work on. word_count is computed at
seed time rather than hand-authored, so it stays correct when content is
edited.

The index mapping is `dynamic: strict` - a document carrying a field that
search/index_config.py doesn't declare is rejected outright rather than
silently mapped. Add the field there first.

Usage:
    python scripts/seed_data.py
    python scripts/seed_data.py --recreate   # delete the index first
"""

import argparse
import re

from hybrid_search_api.config import get_settings
from hybrid_search_api.search.elasticsearch_client import build_client, ensure_index
from hybrid_search_api.search.embeddings import embed_many

SAMPLE_DOCS = [
    {
        "title": "Elasticsearch Basics",
        "category": "fundamentals",
        "tags": ["elasticsearch", "lucene", "indexing"],
        "published": "2023-06-12",
        "source": "handbook",
        "content": (
            "Elasticsearch is a distributed search and analytics engine built on top of "
            "Apache Lucene. It is suited for full-text search, structured search, and "
            "near-real-time analytics. Data is organized into indices, which are "
            "internally distributed across multiple shards."
        ),
    },
    {
        "title": "Vector Search and Embeddings",
        "category": "vector-search",
        "tags": ["embeddings", "vector-search", "semantics"],
        "published": "2023-08-03",
        "source": "handbook",
        "content": (
            "Vector search represents text as high-dimensional numeric vectors "
            "(embeddings). Similar content lies close together in vector space, which "
            "means semantically related documents can be found even when there is no "
            "literal word match."
        ),
    },
    {
        "title": "Retrieval-Augmented Generation (RAG)",
        "category": "rag",
        "tags": ["rag", "llm", "grounding"],
        "published": "2023-10-19",
        "source": "handbook",
        "content": (
            "RAG combines a search component with a language model: relevant documents "
            "are retrieved first, then the model generates an answer based on those "
            "sources. This reduces hallucinations and makes answers traceable."
        ),
    },
    {
        "title": "BM25 Ranking",
        "category": "lexical-search",
        "tags": ["bm25", "ranking", "tf-idf"],
        "published": "2023-12-07",
        "source": "handbook",
        "content": (
            "BM25 is a ranking function for classic full-text search that takes term "
            "frequency, inverse document frequency, and document length into account. "
            "It is the default scoring algorithm in Elasticsearch and delivers very good "
            "results for exact term matches."
        ),
    },
    {
        "title": "Reciprocal Rank Fusion (RRF)",
        "category": "fusion",
        "tags": ["rrf", "ranking", "hybrid-search"],
        "published": "2024-02-15",
        "source": "field-notes",
        "content": (
            "RRF fuses multiple ranked lists from different search methods without "
            "requiring their scores to be brought onto a common scale. Each document "
            "gets points based on its rank in every list, which makes RRF robust "
            "against outliers."
        ),
    },
    {
        "title": "Approximate Nearest Neighbor Search (HNSW)",
        "category": "vector-search",
        "tags": ["hnsw", "ann", "vector-search", "performance"],
        "published": "2024-04-22",
        "source": "field-notes",
        "content": (
            "For kNN search, Elasticsearch uses the HNSW algorithm (Hierarchical "
            "Navigable Small World) to find similar vectors approximately but very "
            "quickly. The num_candidates parameter controls the balance between search "
            "speed and accuracy."
        ),
    },
    {
        "title": "Sentence Transformer Models",
        "category": "nlp",
        "tags": ["embeddings", "nlp", "transformers"],
        "published": "2024-06-11",
        "source": "handbook",
        "content": (
            "Sentence transformer models like all-MiniLM-L6-v2 turn whole sentences "
            "into embedding vectors instead of considering individual words in "
            "isolation. This lets them capture context and meaning better than classic "
            "word embeddings."
        ),
    },
    {
        "title": "Full-Text Search vs. Semantic Search",
        "category": "fundamentals",
        "tags": ["hybrid-search", "semantics", "bm25"],
        "published": "2024-08-29",
        "source": "handbook",
        "content": (
            "Full-text search finds documents through exact or fuzzy word matches, "
            "while semantic search relies on meaning similarity. Hybrid search combines "
            "both approaches to deliver precise term matches as well as content that is "
            "conceptually related."
        ),
    },
    {
        "title": "Analyzers and Tokenization",
        "category": "lexical-search",
        "tags": ["analyzers", "tokenization", "stemming"],
        "published": "2024-11-05",
        "source": "field-notes",
        "content": (
            "An Elasticsearch analyzer breaks text into tokens and normalizes them, for "
            "example through lowercasing, stemming, or stopword removal. "
            "Language-specific analyzers, such as the German analyzer, noticeably "
            "improve match quality for German-language content."
        ),
    },
    {
        "title": "Prompt Engineering for RAG Systems",
        "category": "rag",
        "tags": ["rag", "prompts", "llm"],
        "published": "2025-01-16",
        "source": "field-notes",
        "content": (
            "How the system prompt is worded largely determines whether a RAG system "
            "answers strictly from the supplied sources or tends toward "
            "hallucinations. Clear instructions, explicit source references, and "
            "prompt versioning all improve traceability."
        ),
    },
]


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the demo documents.")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete the index before seeding. Needed after a mapping change - "
        "ensure_index() only creates a missing index, it never updates one.",
    )
    args = parser.parse_args()

    settings = get_settings()
    client = build_client(settings)
    if args.recreate:
        client.options(ignore_status=[404]).indices.delete(index=settings.elasticsearch_index)
        print(f"Deleted index '{settings.elasticsearch_index}'.")
    ensure_index(client, settings.elasticsearch_index)

    print("Computing embeddings (first run downloads the model, ~80MB)...")
    vectors = embed_many([doc["content"] for doc in SAMPLE_DOCS])

    for i, (doc, vector) in enumerate(zip(SAMPLE_DOCS, vectors, strict=True), start=1):
        client.index(
            index=settings.elasticsearch_index,
            id=str(i),
            document={
                **doc,
                "embedding": vector,
                "url": f"https://kb.local/{slugify(doc['title'])}",
                "word_count": len(doc["content"].split()),
            },
        )
    client.indices.refresh(index=settings.elasticsearch_index)
    print(
        f"Indexed {len(SAMPLE_DOCS)} sample documents (with embeddings) "
        f"into '{settings.elasticsearch_index}'."
    )


if __name__ == "__main__":
    main()
