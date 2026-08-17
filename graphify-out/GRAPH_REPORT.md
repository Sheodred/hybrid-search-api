# Graph Report - feat+agentic-rag-mcp  (2026-08-17)

## Corpus Check
- 58 files · ~41,800 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 277 nodes · 529 edges · 20 communities (19 shown, 1 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 26 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `43a26c32`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- answering.py
- index_routes.py
- Architecture (English)
- hybrid_search.py
- SearchResponse
- test_api.py
- Swagger UI Screenshot
- ADR-0001: Local sentence-transformers for embeddings, not Ollama
- Agentic RAG via in-process MCP dogfooding
- config.py
- embeddings.py
- _test_env
- hybrid-search-api
- Settings
- Global Constraints

## God Nodes (most connected - your core abstractions)
1. `Settings` - 36 edges
2. `SearchRequest` - 25 edges
3. `answer_search()` - 25 edges
4. `SearchResponse` - 15 edges
5. `LLMClient` - 14 edges
6. `Architecture (English)` - 13 edges
7. `build_client()` - 12 edges
8. `hybrid-search-api CLAUDE.md` - 12 edges
9. `SearchHit` - 11 edges
10. `agentic_answer_search()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `/verify Command` --semantically_similar_to--> `Contributing Guide`  [INFERRED] [semantically similar]
  .claude/commands/verify.md → CONTRIBUTING.md
- `CI GitHub Actions Workflow` --semantically_similar_to--> `Contributing Guide`  [INFERRED] [semantically similar]
  .github/workflows/ci.yml → CONTRIBUTING.md
- `RAG Grounding Example (README)` --semantically_similar_to--> `RAG Answer Synthesis Pattern`  [INFERRED] [semantically similar]
  README.md → docs/architecture.md
- `RAG Grounding Example (README, DE)` --semantically_similar_to--> `RAG Grounding Example (README)`  [INFERRED] [semantically similar]
  README.de.md → README.md
- `_ScriptedLLMClient` --uses--> `Settings`  [INFERRED]
  tests/test_agentic_answering.py → src/hybrid_search_api/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Local Verification Workflow (pytest + ruff)** — claude_commands_verify_verify_command, contributing_contributing_guide, github_workflows_ci_ci_workflow, pre_commit_config_pre_commit_hooks [INFERRED 0.85]
- **Agent Skills Documentation Set** — claude_project_instructions, docs_agents_domain_domain_docs_consumption, docs_agents_issue_tracker_issue_tracker_conventions, docs_agents_triage_labels_triage_label_mapping [EXTRACTED 1.00]
- **Session Startup Routine** — claude_commands_startup_startup_command, claude_graphify_workflow, claude_handoff_doc_workflow, docs_agents_issue_tracker_issue_tracker_conventions [EXTRACTED 1.00]

## Communities (20 total, 1 thin omitted)

### Community 0 - "answering.py"
Cohesion: 0.09
Nodes (25): ClientSession, retry, LLMClient, Thin wrapper around an OpenAI-compatible chat completions endpoint. Works…, Single non-streaming completion, with automatic retry on transient API errors., Multi-turn completion with optional tool-calling. Returns the raw response…, Yields text chunks as they arrive - use for a responsive, incremental UI., build_agentic_system_prompt() (+17 more)

### Community 1 - "index_routes.py"
Cohesion: 0.36
Nodes (10): BaseModel, elasticsearch_health(), index_info(), list_documents(), get, Introspection endpoints: Elasticsearch cluster health, index info, and a way to…, DocumentListResponse, DocumentPreview (+2 more)

### Community 2 - "Architecture (English)"
Cohesion: 0.07
Nodes (37): ai/prompts.py, api/routes.py, /rebuild Command, /startup Command, /verify Command, Graphify Knowledge Graph Workflow, Handoff Document Workflow, hybrid-search-api CLAUDE.md (+29 more)

### Community 3 - "hybrid_search.py"
Cohesion: 0.18
Nodes (15): _bm25_search(), hybrid_search(), _knn_search(), Elasticsearch, Hybrid search: combines classic BM25 full-text search with kNN vector search…, Run BM25 (+ optionally kNN) search and fuse the results with RRF. Falls back to…, _reciprocal_rank_fusion(), bm25_query() (+7 more)

### Community 4 - "SearchResponse"
Cohesion: 0.36
Nodes (11): SimpleNamespace, SearchHit, SearchResponse, agentic_answer_search(), _message(), patch, _ScriptedLLMClient, test_agentic_loop_answers_without_calling_tool() (+3 more)

### Community 5 - "test_api.py"
Cohesion: 0.09
Nodes (25): ESConnectionError, exception_handler, FileResponse, JSONResponse, Request, get, search_ui(), es_connection_error_handler() (+17 more)

### Community 6 - "Swagger UI Screenshot"
Cohesion: 0.27
Nodes (11): DocumentListResponse schema, DocumentPreview schema, ElasticsearchHealth schema, GET /health/elasticsearch endpoint, GET /health endpoint, HTTPValidationError schema, GET /index/documents endpoint, GET /index endpoint (+3 more)

### Community 7 - "ADR-0001: Local sentence-transformers for embeddings, not Ollama"
Cohesion: 0.17
Nodes (10): ADR-0001: Local sentence-transformers for embeddings, not Ollama, Consequences, Context, Decision, Options considered, ADR-0002: llama-server (not Ollama) for the local/data-sovereignty LLM deployment mode, Consequences, Context (+2 more)

### Community 8 - "Agentic RAG via in-process MCP dogfooding"
Cohesion: 0.17
Nodes (11): Agentic RAG via in-process MCP dogfooding, Approach, Context, Error handling, Goals, `LLMClient` addition, New module: `search/agentic_answering.py`, Non-goals (+3 more)

### Community 9 - "config.py"
Cohesion: 0.10
Nodes (25): Path, main(), Utility script: indexes a small set of sample documents into Elasticsearch,…, download_and_extract(), load_corpus(), main(), Opt-in utility script: downloads the NFCorpus subset of the BEIR benchmark…, get_settings() (+17 more)

### Community 10 - "embeddings.py"
Cohesion: 0.24
Nodes (10): SentenceTransformer, embed(), embed_many(), _get_model(), Sentence-embedding helper for the kNN side of hybrid search. Uses a small local…, Returns the embedding vector for a single piece of text., Batched embedding - more efficient than calling embed() in a loop., patch (+2 more)

### Community 11 - "_test_env"
Cohesion: 0.50
Nodes (3): fixture, Ensure Settings() can be instantiated in tests without a real .env file., _test_env()

### Community 18 - "Settings"
Cohesion: 0.24
Nodes (21): BaseSettings, post, health(), get, search(), Central application configuration, populated from environment variables / .env., Settings, SearchRequest (+13 more)

### Community 19 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Agentic RAG Implementation Plan, Global Constraints, Task 1: Add `anyio` as an explicit dependency, Task 2: Add `agentic` field to `SearchRequest`, Task 3: Add `LLMClient.complete_with_tools()`, Task 4: Add agentic system prompt, Task 5: `search/agentic_answering.py` - the tool-calling loop, Task 6: Wire `answer_search()` to branch on `request.agentic` (+2 more)

## Ambiguous Edges - Review These
- `CI GitHub Actions Workflow` → `hybrid-search-api CLAUDE.md`  [AMBIGUOUS]
  .github/workflows/ci.yml · relation: conceptually_related_to

## Knowledge Gaps
- **39 isolated node(s):** `hybrid-search-api`, `Context`, `Decision`, `Options considered`, `Consequences` (+34 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `CI GitHub Actions Workflow` and `hybrid-search-api CLAUDE.md`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Settings` connect `Settings` to `answering.py`, `index_routes.py`, `SearchResponse`, `config.py`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `answer_search()` connect `Settings` to `answering.py`, `hybrid_search.py`, `SearchResponse`, `config.py`, `embeddings.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `LLMClient` connect `answering.py` to `Settings`, `SearchResponse`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Settings` (e.g. with `LLMClient` and `_ScriptedLLMClient`) actually correct?**
  _`Settings` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `SearchRequest` (e.g. with `_ScriptedLLMClient` and `_FakeLLMClient`) actually correct?**
  _`SearchRequest` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `SearchResponse` (e.g. with `_ScriptedLLMClient` and `_FakeLLMClient`) actually correct?**
  _`SearchResponse` has 3 INFERRED edges - model-reasoned connections that need verification._