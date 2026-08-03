from fastapi import FastAPI

from hybrid_search_api.api.routes import router

app = FastAPI(
    title="Hybrid Search API",
    description="Elasticsearch hybrid search (BM25 + kNN) with an LLM layer for RAG-style answers.",
    version="0.1.0",
)
app.include_router(router)
