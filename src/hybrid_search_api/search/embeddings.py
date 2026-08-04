"""Sentence-embedding helper for the kNN side of hybrid search.

Uses a small local sentence-transformers model - no extra API key, no
per-call cost, works offline after the first download. Swap MODEL_NAME for
a bigger model later if retrieval quality needs it; just make sure the ES
mapping's `dims` in elasticsearch_client.py matches the new model's output
size.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dims - matches the ES mapping


@lru_cache
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed(text: str) -> list[float]:
    """Returns the embedding vector for a single piece of text."""
    return _get_model().encode(text, normalize_embeddings=True).tolist()


def embed_many(texts: list[str]) -> list[list[float]]:
    """Batched embedding - more efficient than calling embed() in a loop."""
    return _get_model().encode(texts, normalize_embeddings=True).tolist()
