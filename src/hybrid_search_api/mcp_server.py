"""MCP server exposing this project's hybrid search as a tool for MCP clients
(Claude Desktop, Claude Code, etc.) - an additional entry point alongside the
REST API, reusing the same answer_search() logic unchanged.

Run with: python -m hybrid_search_api.mcp_server (stdio transport)
"""

from mcp.server.mcpserver import MCPServer

from hybrid_search_api.config import get_settings
from hybrid_search_api.models import SearchRequest

mcp = MCPServer("hybrid-search-api")


@mcp.tool()
def search(query: str, top_k: int = 10, use_llm_answer: bool = True, lang: str = "en") -> dict:
    """Run hybrid (BM25 + kNN) search against the configured Elasticsearch index,
    optionally synthesizing a RAG-style answer from the top results."""
    from hybrid_search_api.search.answering import answer_search

    request = SearchRequest(query=query, top_k=top_k, use_llm_answer=use_llm_answer, lang=lang)
    response = answer_search(request, get_settings())
    return response.model_dump()


if __name__ == "__main__":
    mcp.run()
