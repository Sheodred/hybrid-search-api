from elasticsearch import Elasticsearch

from hybrid_search_api.config import Settings

INDEX_MAPPING = {
    "properties": {
        "title": {"type": "text"},
        "content": {"type": "text"},
        "embedding": {
            "type": "dense_vector",
            "dims": 384,
            "index": True,
            "similarity": "cosine",
        },
    }
}


def build_client(settings: Settings) -> Elasticsearch:
    """Create an Elasticsearch client from settings. Supports both no-auth (local dev)
    and API-key auth (cloud/production)."""
    if settings.elasticsearch_api_key:
        return Elasticsearch(settings.elasticsearch_url, api_key=settings.elasticsearch_api_key)
    return Elasticsearch(settings.elasticsearch_url)


def ensure_index(client: Elasticsearch, index_name: str) -> None:
    """Create the index with the expected mapping if it doesn't exist yet."""
    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name, mappings=INDEX_MAPPING)
