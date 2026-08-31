from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SearchFilters(BaseModel):
    """Structured narrowing applied to both sides of hybrid search.

    Every field is optional; the ones that are set become an Elasticsearch
    filter context (see queries.filter_clauses). Filter context means these
    clauses decide *whether* a document can match, never *how well* - they
    contribute no score and are cacheable.
    """

    category: list[str] | None = Field(default=None, description="Match any of these categories")
    tags: list[str] | None = Field(default=None, description="Match any of these tags")
    source: list[str] | None = Field(default=None, description="Match any of these sources")
    published_after: date | None = Field(default=None, description="Published on or after (YYYY-MM-DD)")
    published_before: date | None = Field(default=None, description="Published on or before (YYYY-MM-DD)")
    min_word_count: int | None = Field(default=None, ge=0, description="Minimum document length in words")
    max_word_count: int | None = Field(default=None, ge=0, description="Maximum document length in words")


class FacetBucket(BaseModel):
    key: str | int
    doc_count: int


class WordCountStats(BaseModel):
    count: int
    min: float | None = None
    max: float | None = None
    avg: float | None = None


class SearchRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "How does vector search work?",
                    "top_k": 5,
                    "use_llm_answer": True,
                    "filters": {"category": ["vector-search"], "min_word_count": 30},
                }
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
    dataset: Literal["demo", "nfcorpus"] = Field(
        default="demo",
        description=(
            "Which indexed corpus to search: 'demo' (10 curated docs about this "
            "project's own search/RAG concepts) or 'nfcorpus' (~3.6K medical "
            "documents from the NFCorpus IR benchmark)"
        ),
    )
    filters: SearchFilters | None = Field(
        default=None,
        description="Optional metadata filters applied to both the BM25 and the kNN side",
    )


class SearchHit(BaseModel):
    id: str
    score: float
    title: str
    content: str
    highlights: list[str] | None = Field(
        default=None,
        description=(
            "Matching snippets from content, with the matched terms wrapped in <em>. "
            "Absent for hits that only the vector side found - there is no lexical "
            "match to highlight."
        ),
    )


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
    answer: str | None = None
    facets: dict[str, list[FacetBucket]] | None = Field(
        default=None,
        description=(
            "Bucket counts over the BM25 match set under the active filters - "
            "not over the fused result set. See docs/search/README.md."
        ),
    )
    word_count_stats: WordCountStats | None = None


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
