from fastapi import FastAPI
from fastapi.responses import JSONResponse

from hybrid_search_api.api.routes import router


class UTF8JSONResponse(JSONResponse):
    """JSON response with an explicit charset for older HTTP clients."""

    media_type = "application/json; charset=utf-8"


tags_metadata = [
    {"name": "search", "description": "Hybrid (BM25 + kNN) search and RAG-style answers."},
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
