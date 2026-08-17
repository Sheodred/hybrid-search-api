# Agentic RAG via in-process MCP dogfooding

Status: approved, not yet implemented
Date: 2026-08-17
Follows: PR #8 (MCP server, merged to `main` at `3aedcfa`)

## Context

`answer_search()` (`search/answering.py`) currently runs a fixed pipeline:
embed query -> hybrid search -> optionally hand the top hits to the LLM to
write a source-grounded answer. The LLM never decides *whether* or *how* to
search - it only writes prose from results it's handed.

This adds a second, opt-in mode where the LLM itself decides when to call
search (and can call it more than once, e.g. to refine a vague query),
using the `search` tool this project already exposes via MCP (PR #8) -
called in-process through a real MCP client/server session, not
re-implemented as a separate local function call.

## Goals

- LLM decides whether/how to invoke search, instead of a fixed pipeline.
- Reuse the existing MCP `search` tool as the mechanism (dogfooding, not a
  parallel implementation) - MCP is now genuinely justified here, because
  the caller is dynamic (the LLM), unlike a same-process fixed pipeline
  call, which is the case PR #8 correctly did *not* use MCP for.
- Zero behavior change to the existing fixed pipeline; this is additive.

## Non-goals

- Not a general-purpose agent framework. One tool (`search`), one bounded
  loop, no planning/memory beyond a single request.
- Not changing the MCP server itself (`mcp_server.py`) - it's reused as-is.

## Approach

### Request shape

Add one field to `SearchRequest`:

```python
agentic: bool = Field(default=False, description="If true, let the LLM decide when/how to call search instead of running a fixed pipeline")
```

Default `False` preserves today's exact behavior untouched. `answer_search()`
branches at the top:

```python
def answer_search(request, settings, llm_client=None):
    if request.agentic:
        return agentic_answer_search(request, settings, llm_client)
    # ... existing fixed pipeline, unchanged
```

### New module: `search/agentic_answering.py`

Houses `agentic_answer_search(request, settings, llm_client=None) -> SearchResponse`.

**MCP session setup** - per request, using the SDK's in-memory transport
(`mcp.shared.memory.create_client_server_memory_streams`), not stdio/subprocess:
an `anyio` task group runs the existing `mcp_server.mcp` server's `run()`
against one end of the memory stream pair while an MCP `ClientSession` talks
to the other end, in the same process. No subprocess spawn, no reloading the
embedding model per request - this is purely a protocol-shaped call, not a
process boundary.

**Tool schema handoff** - `session.list_tools()` returns the real `search`
tool schema (name, description, input schema), converted to the OpenAI
tool-calling format and passed to the LLM. The schema is discovered from the
live MCP server, not hand-duplicated - if the tool's parameters change, this
path picks it up automatically.

**Tool-calling loop** (capped at 3 rounds):

1. Send the conversation (system prompt + user query + any prior tool
   results) to the LLM with `tools=[search_tool_schema]`.
2. If the response requests a tool call: execute it via
   `session.call_tool("search", args)` (real MCP call, not a direct Python
   call), append the result to the conversation, go to 1.
3. If the response has no tool call: treat its content as the final answer,
   stop.
4. After 3 rounds with no final answer, drop `tools` from the next call to
   force a text-only response and stop.
   `# ponytail: fixed 3-round cap, make configurable if real usage needs deeper loops`

The LLM is instructed (system prompt) to call `search` with
`use_llm_answer=False` - it synthesizes the final answer itself from raw
hits, rather than nesting a RAG answer inside the tool call.

**Response assembly** - `hits` in the returned `SearchResponse` come from
the last successful `search` tool call's results (already the same
`SearchHit`-shaped dicts the tool returns); `answer` is the LLM's final
text. If the LLM never calls the tool (e.g. answers from general knowledge),
`hits` is empty and `answer` is still returned.

### `LLMClient` addition

`complete()` only sends a fixed system+user pair and returns text - it has
no tool-calling support. Add one new method:

```python
def complete_with_tools(self, messages: list[dict], tools: list[dict], max_tokens: int = 1024):
    """Multi-turn completion with tool-calling; returns the raw response message
    so the caller can inspect tool_calls."""
```

Same retry decorator as `complete()`. `messages` is the full running
conversation (system/user/assistant/tool roles) since the loop is
multi-turn, unlike `complete()`'s single system+prompt shape.

### Error handling

Unchanged contract: `openai` SDK exceptions (`AuthenticationError`,
`NotFoundError`, `APIStatusError`, `APIError`) still propagate unchanged
from `LLMClient` call sites, exactly like today, so `api/routes.py`'s
existing HTTP translation requires zero changes.

### Testing

Follows the existing `_FakeLLMClient` pattern (`tests/test_answering.py`):
a fake LLM client returns a scripted sequence of responses (tool call, then
final text) so the *real* in-memory MCP client/server session and the real
`search` tool run underneath - only `answer_search` (called inside the
`search` tool) is mocked, same as `tests/test_mcp_server.py` already does.
This exercises the actual MCP wiring (schema discovery, `call_tool`
serialization/deserialization), not just a mocked-away stand-in for it.

Cases to cover:
- LLM calls `search` once, then answers -> hits populated, answer returned.
- LLM answers without calling the tool -> empty hits, answer returned.
- Loop hits the 3-round cap -> forced text-only final call, no crash.
- `agentic=False` (default) -> byte-identical behavior to before this change
  (existing `test_answering.py` tests keep passing unmodified).

## Open questions / deferred

- `top_k` from the request is not force-passed into the LLM's tool calls;
  the LLM uses the tool's own default unless the system prompt nudges it.
  Fine to leave advisory-only for now; revisit if it matters in practice.
- No streaming support for the agentic path in this iteration - `complete_with_tools`
  is non-streaming, matching `complete()`, not `stream()`.
