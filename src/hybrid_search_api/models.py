from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"query": "How does vector search work?", "top_k": 5, "use_llm_answer": True}
            ]
        }
    )

    query: str = Field(..., min_length=1, description="Natural-language search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    use_llm_answer: bool = Field(
        default=True,
        description="If true, synthesize a RAG-style answer from the top results",
    )
    lang: Literal["en", "de"] = Field(
        default="en",
        description="Language for the RAG answer and error messages: English (default) or German",
    )
    agentic: bool = Field(
        default=False,
        description=(
            "If true, let the LLM decide when/how to call search instead of "
            "running a fixed pipeline"
        ),
    )


class SearchHit(BaseModel):
    id: str
    score: float
    title: str
    content: str


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
    answer: str | None = None


class ElasticsearchHealth(BaseModel):
    status: str
    cluster_name: str
    number_of_nodes: int
    active_shards: int
    unassigned_shards: int


class IndexInfo(BaseModel):
    index: str
    exists: bool
    document_count: int | None = None
    mapping: dict | None = None


class DocumentPreview(BaseModel):
    id: str
    title: str
    content: str


class DocumentListResponse(BaseModel):
    total: int
    documents: list[DocumentPreview]
