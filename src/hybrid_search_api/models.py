from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"query": "Wie funktioniert Vektorsuche?", "top_k": 5, "use_llm_answer": True}
            ]
        }
    )

    query: str = Field(..., min_length=1, description="Natural-language search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    use_llm_answer: bool = Field(
        default=True,
        description="If true, synthesize a RAG-style answer from the top results",
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
