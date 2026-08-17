# Agentic RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in `agentic` search mode where the LLM decides when/how to call search (via the project's own MCP `search` tool, in-process) instead of always running the fixed embed -> search -> answer pipeline.

**Architecture:** New module `search/agentic_answering.py` runs an in-process MCP client/server session (SDK's in-memory transport, no subprocess) against the existing `mcp_server.mcp` instance, drives an OpenAI-style tool-calling loop capped at 3 rounds, and returns a `SearchResponse`. `answer_search()` branches to it when `request.agentic` is `True`; default behavior is unchanged.

**Tech Stack:** Python 3.11+, `mcp` SDK (already a dependency, added in PR #8), `anyio` (already transitively available, will be declared explicitly), `openai` SDK's tool-calling API, pytest.

**Spec:** `docs/superpowers/specs/2026-08-17-agentic-rag-mcp-design.md`

## Global Constraints

- Default (`agentic=False`) behavior must stay byte-identical to today - existing `tests/test_answering.py` tests must keep passing unmodified.
- Tool-call loop capped at 3 rounds; after that, force one final text-only call and stop (`# ponytail:` comment required at the cap constant).
- `openai` SDK exceptions must keep propagating unchanged from LLM call sites (no new exception translation).
- No subprocess/stdio transport for the internal MCP session - in-memory only.
- `LLMClient.complete_with_tools()` must call `search` tool with `use_llm_answer=False` per the agentic system prompt instruction (tested indirectly via the scripted-LLM tests, not asserted on the prompt text itself).

---

### Task 1: Add `anyio` as an explicit dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add the dependency**

In `pyproject.toml`, in the `dependencies` list (already includes `"mcp>=2.0"`), add:

```toml
    "anyio>=4.0",
```

- [ ] **Step 2: Install and verify**

Run: `.venv/Scripts/python -m pip install -e .`
Expected: installs cleanly (already present transitively, this just pins it explicitly)

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: declare anyio as an explicit dependency"
```

---

### Task 2: Add `agentic` field to `SearchRequest`

**Files:**
- Modify: `src/hybrid_search_api/models.py`

**Interfaces:**
- Produces: `SearchRequest.agentic: bool` (default `False`), consumed by Task 6.

- [ ] **Step 1: Write failing test**

Add to `tests/test_answering.py` (near the top, after imports):

```python
def test_search_request_agentic_defaults_to_false():
    from hybrid_search_api.models import SearchRequest

    assert SearchRequest(query="test").agentic is False
```

- [ ] **Step 2: Run test, verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_answering.py::test_search_request_agentic_defaults_to_false -v`
Expected: FAIL with `AttributeError` or a pydantic validation-related error (field doesn't exist yet, so `.agentic` access fails)

- [ ] **Step 3: Add the field**

In `src/hybrid_search_api/models.py`, inside `class SearchRequest(BaseModel):`, after the `lang` field:

```python
    agentic: bool = Field(
        default=False,
        description=(
            "If true, let the LLM decide when/how to call search instead of "
            "running a fixed pipeline"
        ),
    )
```

- [ ] **Step 4: Run test, verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_answering.py::test_search_request_agentic_defaults_to_false -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/hybrid_search_api/models.py tests/test_answering.py
git commit -m "feat: add agentic field to SearchRequest"
```

---

### Task 3: Add `LLMClient.complete_with_tools()`

**Files:**
- Modify: `src/hybrid_search_api/ai/llm_client.py`
- Test: `tests/test_llm_client.py`

**Interfaces:**
- Produces: `LLMClient.complete_with_tools(messages: list[dict], tools: list[dict] | None, max_tokens: int = 1024) -> openai.types.chat.ChatCompletionMessage` (the raw response message, so the caller can read `.content` and `.tool_calls`), consumed by Task 5.

- [ ] **Step 1: Write failing test**

Add to `tests/test_llm_client.py`:

```python
@patch("hybrid_search_api.ai.llm_client.OpenAI")
def test_complete_with_tools_returns_raw_message(mock_openai_cls):
    mock_message = MagicMock(content="Test", tool_calls=None)
    mock_choice = MagicMock(message=mock_message)
    mock_response = MagicMock(choices=[mock_choice])
    mock_openai_cls.return_value.chat.completions.create.return_value = mock_response

    client = LLMClient(Settings())
    tools = [{"type": "function", "function": {"name": "x", "parameters": {}}}]
    result = client.complete_with_tools(
        messages=[{"role": "user", "content": "hi"}], tools=tools
    )

    assert result is mock_message
    _, kwargs = mock_openai_cls.return_value.chat.completions.create.call_args
    assert kwargs["tools"] == tools


@patch("hybrid_search_api.ai.llm_client.OpenAI")
def test_complete_with_tools_omits_tools_kwarg_when_none(mock_openai_cls):
    mock_message = MagicMock(content="Test", tool_calls=None)
    mock_choice = MagicMock(message=mock_message)
    mock_response = MagicMock(choices=[mock_choice])
    mock_openai_cls.return_value.chat.completions.create.return_value = mock_response

    client = LLMClient(Settings())
    client.complete_with_tools(messages=[{"role": "user", "content": "hi"}], tools=None)

    _, kwargs = mock_openai_cls.return_value.chat.completions.create.call_args
    assert "tools" not in kwargs
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `.venv/Scripts/python -m pytest tests/test_llm_client.py -v`
Expected: FAIL with `AttributeError: 'LLMClient' object has no attribute 'complete_with_tools'`

- [ ] **Step 3: Implement**

In `src/hybrid_search_api/ai/llm_client.py`, add this method to `LLMClient` (after `complete`, before `stream`):

```python
    @retry(
        retry=retry_if_exception_type((APIError, APIStatusError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def complete_with_tools(
        self, messages: list[dict], tools: list[dict] | None, max_tokens: int = 1024
    ):
        """Multi-turn completion with optional tool-calling. Returns the raw response
        message so the caller can inspect .content and .tool_calls."""
        kwargs = {"model": self._model, "max_tokens": max_tokens, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        try:
            response = self._client.chat.completions.create(**kwargs)
            return response.choices[0].message
        except (APIError, APIStatusError):
            logger.exception("LLM API call failed")
            raise
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `.venv/Scripts/python -m pytest tests/test_llm_client.py -v`
Expected: PASS (all tests in file)

- [ ] **Step 5: Commit**

```bash
git add src/hybrid_search_api/ai/llm_client.py tests/test_llm_client.py
git commit -m "feat: add tool-calling support to LLMClient"
```

---

### Task 4: Add agentic system prompt

**Files:**
- Modify: `src/hybrid_search_api/ai/prompts.py`
- Test: `tests/test_prompts.py`

**Interfaces:**
- Produces: `build_agentic_system_prompt(lang: str = "en") -> str`, consumed by Task 5.

- [ ] **Step 1: Write failing test**

Add to `tests/test_prompts.py`:

```python
from hybrid_search_api.ai.prompts import build_agentic_system_prompt


def test_agentic_system_prompt_instructs_no_nested_llm_answer_en():
    prompt = build_agentic_system_prompt(lang="en")

    assert "use_llm_answer" in prompt
    assert "false" in prompt.lower()


def test_agentic_system_prompt_instructs_no_nested_llm_answer_de():
    prompt = build_agentic_system_prompt(lang="de")

    assert "use_llm_answer" in prompt
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `.venv/Scripts/python -m pytest tests/test_prompts.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_agentic_system_prompt'`

- [ ] **Step 3: Implement**

In `src/hybrid_search_api/ai/prompts.py`, add after the existing `_USER_PROMPT_TEMPLATE` dict (before `build_rag_prompt`):

```python
AGENTIC_SYSTEM_V1_EN = """\
You can call the `search` tool to look up information before answering.
When you call it, always set use_llm_answer to false - you will write the
final answer yourself from the raw search results, not the tool.
Call search as many times as needed to answer well, but don't call it
needlessly if you already know the answer.
Once you have enough information, answer concisely in plain prose - no
markdown formatting (no headings, bold, or tables) - and state what your
answer is based on (e.g. document title).
"""

AGENTIC_SYSTEM_V1_DE = """\
Du kannst das Tool `search` nutzen, um vor der Antwort Informationen
nachzuschlagen. Setze beim Aufruf immer use_llm_answer auf false - du
schreibst die endgueltige Antwort selbst anhand der rohen Suchergebnisse,
nicht das Tool.
Rufe search so oft wie noetig auf, aber nicht unnoetig, wenn du die Antwort
bereits kennst.
Sobald du genug Informationen hast, antworte knapp in reinem Fliesstext -
kein Markdown (keine Ueberschriften, Fettungen oder Tabellen) - und nenne,
worauf sich deine Antwort stuetzt (z. B. Dokumenttitel).
"""

_AGENTIC_SYSTEM_PROMPTS = {"en": AGENTIC_SYSTEM_V1_EN, "de": AGENTIC_SYSTEM_V1_DE}


def build_agentic_system_prompt(lang: str = "en") -> str:
    return _AGENTIC_SYSTEM_PROMPTS[lang]
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `.venv/Scripts/python -m pytest tests/test_prompts.py -v`
Expected: PASS (all tests in file)

- [ ] **Step 5: Commit**

```bash
git add src/hybrid_search_api/ai/prompts.py tests/test_prompts.py
git commit -m "feat: add agentic system prompt"
```

---

### Task 5: `search/agentic_answering.py` - the tool-calling loop

**Files:**
- Create: `src/hybrid_search_api/search/agentic_answering.py`
- Test: `tests/test_agentic_answering.py`

**Interfaces:**
- Consumes: `LLMClient.complete_with_tools()` (Task 3), `build_agentic_system_prompt()` (Task 4), `hybrid_search_api.mcp_server.mcp` (the `MCPServer` instance from PR #8, unmodified), `hybrid_search_api.models.SearchRequest/SearchHit/SearchResponse`.
- Produces: `agentic_answer_search(request: SearchRequest, settings: Settings, llm_client: LLMClient | None = None) -> SearchResponse`, consumed by Task 6.

This task has three failing-test-then-implement cycles because the loop has three distinct behaviors to prove: calls the tool then answers, answers without calling the tool, and hits the round cap. All three tests are written together first (they share fakes), then the implementation is written once to satisfy all three - splitting the implementation into three separate partial passes would produce throwaway intermediate code, so this task is one red -> one green -> commit cycle covering all three cases.

- [ ] **Step 1: Write the test file (all three cases), verify all fail**

Create `tests/test_agentic_answering.py`:

```python
import json
from types import SimpleNamespace
from unittest.mock import patch

from hybrid_search_api.config import Settings
from hybrid_search_api.models import SearchHit, SearchRequest, SearchResponse
from hybrid_search_api.search.agentic_answering import agentic_answer_search


def _tool_call(call_id: str, name: str, arguments: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=call_id, function=SimpleNamespace(name=name, arguments=json.dumps(arguments))
    )


def _message(content: str | None = None, tool_calls: list | None = None) -> SimpleNamespace:
    return SimpleNamespace(content=content, tool_calls=tool_calls or [])


class _ScriptedLLMClient:
    def __init__(self, responses: list[SimpleNamespace]):
        self._responses = list(responses)

    def complete_with_tools(self, messages, tools, max_tokens=1024):
        return self._responses.pop(0)


@patch("hybrid_search_api.mcp_server.answer_search")
def test_agentic_loop_calls_search_then_answers(mock_answer_search):
    mock_answer_search.return_value = SearchResponse(
        query="test", hits=[SearchHit(id="1", score=1.0, title="T", content="C")], answer=None
    )
    llm = _ScriptedLLMClient(
        [
            _message(
                tool_calls=[
                    _tool_call("call1", "search", {"query": "test", "use_llm_answer": False})
                ]
            ),
            _message(content="Final answer."),
        ]
    )

    response = agentic_answer_search(
        SearchRequest(query="test", agentic=True), Settings(), llm_client=llm
    )

    assert response.answer == "Final answer."
    assert response.hits[0].title == "T"


@patch("hybrid_search_api.mcp_server.answer_search")
def test_agentic_loop_answers_without_calling_tool(mock_answer_search):
    llm = _ScriptedLLMClient([_message(content="I already know this.")])

    response = agentic_answer_search(
        SearchRequest(query="test", agentic=True), Settings(), llm_client=llm
    )

    assert response.answer == "I already know this."
    assert response.hits == []
    mock_answer_search.assert_not_called()


@patch("hybrid_search_api.mcp_server.answer_search")
def test_agentic_loop_forces_final_answer_after_round_cap(mock_answer_search):
    mock_answer_search.return_value = SearchResponse(
        query="test", hits=[SearchHit(id="1", score=1.0, title="T", content="C")], answer=None
    )
    tool_call_message = _message(
        tool_calls=[_tool_call("call1", "search", {"query": "test", "use_llm_answer": False})]
    )
    llm = _ScriptedLLMClient(
        [tool_call_message, tool_call_message, tool_call_message, _message(content="Forced answer.")]
    )

    response = agentic_answer_search(
        SearchRequest(query="test", agentic=True), Settings(), llm_client=llm
    )

    assert response.answer == "Forced answer."
```

Note: patching `hybrid_search_api.mcp_server.answer_search` (not a path inside `agentic_answering.py`) is deliberate - `agentic_answering.py` never imports `answer_search` itself, it only talks to the real `mcp_server.mcp` instance over a real in-memory MCP session, whose `search` tool internally calls `answer_search`. This is the same mocking point `tests/test_mcp_server.py` already uses. It also proves the branch in Task 6 doesn't recurse: the `SearchRequest` built inside `mcp_server.search()` never sets `agentic=True`, so it always takes the fixed-pipeline path.

Run: `.venv/Scripts/python -m pytest tests/test_agentic_answering.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'hybrid_search_api.search.agentic_answering'`

- [ ] **Step 2: Implement**

Create `src/hybrid_search_api/search/agentic_answering.py`:

```python
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
```

- [ ] **Step 3: Run tests, verify they pass**

Run: `.venv/Scripts/python -m pytest tests/test_agentic_answering.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 4: Commit**

```bash
git add src/hybrid_search_api/search/agentic_answering.py tests/test_agentic_answering.py
git commit -m "feat: add agentic RAG tool-calling loop via in-process MCP session"
```

---

### Task 6: Wire `answer_search()` to branch on `request.agentic`

**Files:**
- Modify: `src/hybrid_search_api/search/answering.py`
- Test: `tests/test_answering.py`

**Interfaces:**
- Consumes: `agentic_answer_search()` (Task 5).

- [ ] **Step 1: Write failing test**

Add to `tests/test_answering.py`:

```python
@patch("hybrid_search_api.search.answering.agentic_answer_search")
def test_answer_search_dispatches_to_agentic_when_requested(mock_agentic_answer_search):
    expected = SearchResponse(query="test", hits=[], answer="agentic answer")
    mock_agentic_answer_search.return_value = expected

    response = answer_search(SearchRequest(query="test", agentic=True), Settings())

    assert response is expected
    mock_agentic_answer_search.assert_called_once()
```

(`SearchResponse` is already imported indirectly via `hybrid_search_api.models` in this file's existing imports - add `SearchResponse` to the existing `from hybrid_search_api.models import ...` line if not already present.)

- [ ] **Step 2: Run test, verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_answering.py::test_answer_search_dispatches_to_agentic_when_requested -v`
Expected: FAIL with `AttributeError: <module 'hybrid_search_api.search.answering'> does not have the attribute 'agentic_answer_search'` (patch target doesn't exist yet)

- [ ] **Step 3: Implement**

In `src/hybrid_search_api/search/answering.py`:

Add import after the existing `from hybrid_search_api.ai.llm_client import LLMClient` line:

```python
from hybrid_search_api.search.agentic_answering import agentic_answer_search
```

Change the start of `answer_search()` from:

```python
def answer_search(
    request: SearchRequest, settings: Settings, llm_client: LLMClient | None = None
) -> SearchResponse:
    es_client = build_client(settings)
```

to:

```python
def answer_search(
    request: SearchRequest, settings: Settings, llm_client: LLMClient | None = None
) -> SearchResponse:
    if request.agentic:
        return agentic_answer_search(request, settings, llm_client)

    es_client = build_client(settings)
```

- [ ] **Step 4: Run full test suite, verify everything passes**

Run: `.venv/Scripts/python -m pytest -v`
Expected: PASS (all tests, including every existing `test_answering.py` test unmodified - confirms the default path is untouched)

- [ ] **Step 5: Commit**

```bash
git add src/hybrid_search_api/search/answering.py tests/test_answering.py
git commit -m "feat: dispatch to agentic_answer_search when request.agentic is true"
```

---

### Task 7: Lint, full verification, README docs

**Files:**
- Modify: `README.md`
- Modify: `README.de.md`

- [ ] **Step 1: Run full verification**

Run: `.venv/Scripts/python -m pytest -v && .venv/Scripts/python -m ruff check src tests`
Expected: all tests PASS, ruff reports no issues

- [ ] **Step 2: Document the `agentic` flag in README.md**

In `README.md`, in the `## Usage` section, after the existing `POST /search` paragraph (which documents `query`/`top_k`/`use_llm_answer`/`lang`), add:

```markdown
Set `"agentic": true` to let the LLM decide when/how to call search itself
(via this project's own MCP `search` tool, called in-process) instead of
running the fixed search-then-answer pipeline - useful for vague queries
that may need a refined follow-up search. Default is `false` (fixed
pipeline, as above).
```

- [ ] **Step 3: Mirror in README.de.md**

In `README.de.md`, in the `## Nutzung` section, after the existing `POST /search` paragraph, add:

```markdown
Mit `"agentic": true` entscheidet das LLM selbst, wann/wie es die Suche
aufruft (ueber das projekteigene MCP-Tool `search`, in-process aufgerufen)
statt der festen Suche-dann-Antwort-Pipeline zu folgen - sinnvoll bei
vagen Anfragen, die eine verfeinerte Nachsuche brauchen koennten. Standard
ist `false` (feste Pipeline, wie oben).
```

- [ ] **Step 4: Refresh graphify**

Run: `graphify update .`

- [ ] **Step 5: Commit**

```bash
git add README.md README.de.md graphify-out
git commit -m "docs: document the agentic search mode"
```

---

### Task 8: Live end-to-end verification

Not a code change - a manual verification step before opening the PR, matching how PR #8 was verified.

- [ ] **Step 1: Ensure Elasticsearch is running and seeded**

Run: `docker compose up -d elasticsearch` (if not already up), then `.venv/Scripts/python scripts/seed_data.py` (if not already seeded)

- [ ] **Step 2: Call the real endpoint with `agentic: true`**

Run (PowerShell):
```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/search -ContentType "application/json" -Body '{"query": "How does vector search work?", "agentic": true}'
```

(Requires the API running - `docker compose up -d --build api` first, or run `uvicorn hybrid_search_api.main:app` locally against the same `.env`.)

Expected: a real response with non-empty `hits` and a coherent `answer`, produced via at least one real tool-call round-trip (visible in API logs as an MCP `call_tool` reaching the real `hybrid_search` code path).

- [ ] **Step 3: Report result to the user**

State whether the live call succeeded, what the LLM actually answered, and how many tool-call rounds it used (visible in logs) before opening the PR.
