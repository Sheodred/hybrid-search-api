"""Introspection endpoints: Elasticsearch cluster health, index info, and a
way to browse indexed documents directly - useful for testing and demos
without needing curl or Kibana on the side.

No authentication on these by design (see README roadmap) - fine for a
demo/portfolio instance, would need protecting for real production use.
"""

from fastapi import APIRouter, Depends, Query

from hybrid_search_api.config import Settings, get_settings
from hybrid_search_api.models import (
    DocumentListResponse,
    DocumentPreview,
    ElasticsearchHealth,
    IndexInfo,
)
from hybrid_search_api.search.elasticsearch_client import build_client

router = APIRouter()


@router.get(
    "/health/elasticsearch",
    tags=["ops"],
    summary="Elasticsearch cluster health",
    response_model=ElasticsearchHealth,
)
def elasticsearch_health(settings: Settings = Depends(get_settings)) -> ElasticsearchHealth:
    client = build_client(settings)
    health = client.cluster.health()
    return ElasticsearchHealth(
        status=health["status"],
        cluster_name=health["cluster_name"],
        number_of_nodes=health["number_of_nodes"],
        active_shards=health["active_shards"],
        unassigned_shards=health["unassigned_shards"],
    )


@router.get(
    "/index",
    tags=["index"],
    summary="Index info: mapping and document count",
    response_model=IndexInfo,
)
def index_info(settings: Settings = Depends(get_settings)) -> IndexInfo:
    client = build_client(settings)
    index_name = settings.elasticsearch_index
    if not client.indices.exists(index=index_name):
        return IndexInfo(index=index_name, exists=False)
    count = client.count(index=index_name)["count"]
    mapping = client.indices.get_mapping(index=index_name)[index_name]["mappings"]
    return IndexInfo(index=index_name, exists=True, document_count=count, mapping=mapping)


@router.get(
    "/index/documents",
    tags=["index"],
    summary="Browse indexed documents",
    description=(
        "Paginated list of documents currently in the index - lets you inspect "
        "what's actually searchable without a separate Elasticsearch client."
    ),
    response_model=DocumentListResponse,
)
def list_documents(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
) -> DocumentListResponse:
    client = build_client(settings)
    resp = client.search(
        index=settings.elasticsearch_index,
        query={"match_all": {}},
        from_=offset,
        size=limit,
    )
    total = resp["hits"]["total"]["value"]
    documents = [
        DocumentPreview(
            id=h["_id"],
            title=h["_source"].get("title", ""),
            content=h["_source"].get("content", ""),
        )
        for h in resp["hits"]["hits"]
    ]
    return DocumentListResponse(total=total, documents=documents)
