import logging

from elasticsearch import ConnectionError as ESConnectionError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from hybrid_search_api.api.index_routes import router as index_router
from hybrid_search_api.api.routes import router

logger = logging.getLogger(__name__)


class UTF8JSONResponse(JSONResponse):
    """JSON response with an explicit charset for older HTTP clients."""

    media_type = "application/json; charset=utf-8"


tags_metadata = [
    {"name": "search", "description": "Hybrid (BM25 + kNN) search and RAG-style answers."},
    {
        "name": "index",
        "description":
            "Introspect the Elasticsearch index: mapping, document count, browse documents.",
    },
    {"name": "ops", "description": "Health and operational endpoints."},
]

app = FastAPI(
    title="Hybrid Search API",
    description="Elasticsearch hybrid search (BM25 + kNN) with an LLM layer for RAG-style answers.",
    version="0.1.0",
    openapi_tags=tags_metadata,
    default_response_class=UTF8JSONResponse,
)
app.include_router(router)
app.include_router(index_router)


@app.exception_handler(ESConnectionError)
async def es_connection_error_handler(request: Request, exc: ESConnectionError) -> UTF8JSONResponse:
    """Applies to every route: if Elasticsearch itself is unreachable, return a
    clear 502 instead of a bare 500 - covers /search too, not just the new
    introspection endpoints."""
    logger.exception("Elasticsearch unreachable")
    return UTF8JSONResponse(
        status_code=502,
        content={"detail": f"Elasticsearch nicht erreichbar (ELASTICSEARCH_URL pruefen): {exc}"},
    )
