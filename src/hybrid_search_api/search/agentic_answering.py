"""Opt-in agentic search mode: instead of the fixed embed -> search -> answer
pipeline in answering.py, the LLM decides whether/how to call search itself,
via the same `search` MCP tool this project exposes externally
(mcp_server.py) - called in-process through a real MCP client/server
session, not a duplicate local implementation.
"""

import json
import logging

import anyio
from mcp import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from hybrid_search_api.ai.llm_client import LLMClient
from hybrid_search_api.ai.prompts import build_agentic_system_prompt
from hybrid_search_api.config import Settings
from hybrid_search_api.mcp_server import mcp as mcp_server_instance
from hybrid_search_api.models import SearchHit, SearchRequest, SearchResponse

logger = logging.getLogger(__name__)

# ponytail: fixed 3-round cap, make configurable if real usage needs deeper loops
_MAX_TOOL_ROUNDS = 3


def _mcp_tools_to_openai_schema(tools: list) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        }
        for tool in tools
    ]


def _assistant_message_from(message) -> dict:
    return {
        "role": "assistant",
        "content": message.content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in message.tool_calls
        ],
    }


async def _execute_tool_call(session: ClientSession, tool_call) -> tuple[str, list[dict] | None]:
    args = json.loads(tool_call.function.arguments)
    result = await session.call_tool(tool_call.function.name, args)
    text = result.content[0].text
    hits = json.loads(text).get("hits")
    return text, hits


async def _run_agentic_loop(
    query: str, lang: str, llm: LLMClient, session: ClientSession, tools: list[dict]
) -> tuple[str, list[dict]]:
    messages = [
        {"role": "system", "content": build_agentic_system_prompt(lang)},
        {"role": "user", "content": query},
    ]
    last_hits: list[dict] = []

    for _ in range(_MAX_TOOL_ROUNDS):
        message = llm.complete_with_tools(messages, tools)
        if not message.tool_calls:
            return message.content or "", last_hits

        messages.append(_assistant_message_from(message))
        for tool_call in message.tool_calls:
            text, hits = await _execute_tool_call(session, tool_call)
            if hits is not None:
                last_hits = hits
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": text})

    final_message = llm.complete_with_tools(messages, tools=None)
    return final_message.content or "", last_hits


def agentic_answer_search(
    request: SearchRequest, settings: Settings, llm_client: LLMClient | None = None
) -> SearchResponse:
    llm = llm_client if llm_client is not None else LLMClient(settings)

    async def _run() -> tuple[str, list[dict]]:
        result: dict = {}
        async with create_client_server_memory_streams() as (client_streams, server_streams):
            client_read, client_write = client_streams
            server_read, server_write = server_streams

            async with anyio.create_task_group() as tg:

                async def run_server() -> None:
                    await mcp_server_instance._lowlevel_server.run(
                        server_read,
                        server_write,
                        mcp_server_instance._lowlevel_server.create_initialization_options(),
                    )

                tg.start_soon(run_server)

                async with ClientSession(client_read, client_write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    tools = _mcp_tools_to_openai_schema(tools_result.tools)
                    result["answer"], result["hits"] = await _run_agentic_loop(
                        request.query, request.lang, llm, session, tools
                    )

                tg.cancel_scope.cancel()

        return result["answer"], result["hits"]

    answer, raw_hits = anyio.run(_run)
    hits = [SearchHit(**h) for h in raw_hits]
    return SearchResponse(query=request.query, hits=hits, answer=answer)
