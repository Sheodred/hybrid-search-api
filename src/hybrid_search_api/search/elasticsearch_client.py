from elasticsearch import Elasticsearch

from hybrid_search_api.config import Settings
from hybrid_search_api.search.index_config import build_index_body


def build_client(settings: Settings) -> Elasticsearch:
    """Create an Elasticsearch client from settings. Supports both no-auth (local dev)
    and API-key auth (cloud/production)."""
    if settings.elasticsearch_api_key:
        return Elasticsearch(settings.elasticsearch_url, api_key=settings.elasticsearch_api_key)
    return Elasticsearch(settings.elasticsearch_url)


def ensure_index(client: Elasticsearch, index_name: str) -> None:
    """Create the index with the configured analyzers/mappings if it doesn't exist yet.

    See search/index_config.py to adjust fields, analyzers, or filters.
    """
    if not client.indices.exists(index=index_name):
        body = build_index_body()
        client.indices.create(
            index=index_name, settings=body["settings"], mappings=body["mappings"]
        )
