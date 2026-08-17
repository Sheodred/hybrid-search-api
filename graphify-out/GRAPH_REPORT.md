# Graph Report - hybrid-search-api  (2026-08-17)

## Corpus Check
- 58 files · ~42,715 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 282 nodes · 556 edges · 20 communities (19 shown, 1 thin omitted)
- Extraction: 94% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 30 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `08b9d18d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Settings
- index_routes.py
- Architecture (English)
- hybrid_search.py
- prompts.py
- test_api.py
- Swagger UI Screenshot
- ADR-0001: Local sentence-transformers for embeddings, not Ollama
- Agentic RAG via in-process MCP dogfooding
- elasticsearch_client.py
- .complete
- _test_env
- hybrid-search-api
- SearchRequest
- Global Constraints

## God Nodes (most connected - your core abstractions)
1. `Settings` - 41 edges
2. `SearchRequest` - 29 edges
3. `answer_search()` - 27 edges
4. `SearchResponse` - 16 edges
5. `LLMClient` - 13 edges
6. `agentic_answer_search()` - 13 edges
7. `Architecture (English)` - 13 edges
8. `SearchHit` - 12 edges
9. `build_client()` - 12 edges
10. `hybrid-search-api CLAUDE.md` - 12 edges

## Surprising Connections (you probably didn't know these)
- `/verify Command` --semantically_similar_to--> `Contributing Guide`  [INFERRED] [semantically similar]
  .claude/commands/verify.md → CONTRIBUTING.md
- `CI GitHub Actions Workflow` --semantically_similar_to--> `Contributing Guide`  [INFERRED] [semantically similar]
  .github/workflows/ci.yml → CONTRIBUTING.md
- `RAG Grounding Example (README)` --semantically_similar_to--> `RAG Answer Synthesis Pattern`  [INFERRED] [semantically similar]
  README.md → docs/architecture.md
- `RAG Grounding Example (README, DE)` --semantically_similar_to--> `RAG Grounding Example (README)`  [INFERRED] [semantically similar]
  README.de.md → README.md
- `_FakeLLMClient` --uses--> `Settings`  [INFERRED]
  tests/test_answering.py → src/hybrid_search_api/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Local Verification Workflow (pytest + ruff)** — claude_commands_verify_verify_command, contributing_contributing_guide, github_workflows_ci_ci_workflow, pre_commit_config_pre_commit_hooks [INFERRED 0.85]
- **Agent Skills Documentation Set** — claude_project_instructions, docs_agents_domain_domain_docs_consumption, docs_agents_issue_tracker_issue_tracker_conventions, docs_agents_triage_labels_triage_label_mapping [EXTRACTED 1.00]
- **Session Startup Routine** — claude_commands_startup_startup_command, claude_graphify_workflow, claude_handoff_doc_workflow, docs_agents_issue_tracker_issue_tracker_conventions [EXTRACTED 1.00]

## Communities (20 total, 1 thin omitted)

### Community 0 - "Settings"
Cohesion: 0.13
Nodes (31): BaseSettings, ClientSession, SimpleNamespace, LLMClient, Thin wrapper around an OpenAI-compatible chat completions endpoint. Works…, Maps a `dataset` selector ("demo"/"nfcorpus") to its ES index name. Mirrors the…, Central application configuration, populated from environment variables / .env., resolve_index() (+23 more)

### Community 1 - "index_routes.py"
Cohesion: 0.32
Nodes (12): BaseModel, elasticsearch_health(), index_info(), list_documents(), get, Introspection endpoints: Elasticsearch cluster health, index info, and a way to…, DocumentListResponse, DocumentPreview (+4 more)

### Community 2 - "Architecture (English)"
Cohesion: 0.07
Nodes (37): ai/prompts.py, api/routes.py, /rebuild Command, /startup Command, /verify Command, Graphify Knowledge Graph Workflow, Handoff Document Workflow, hybrid-search-api CLAUDE.md (+29 more)

### Community 3 - "hybrid_search.py"
Cohesion: 0.18
Nodes (15): _bm25_search(), hybrid_search(), _knn_search(), Elasticsearch, Hybrid search: combines classic BM25 full-text search with kNN vector search…, Run BM25 (+ optionally kNN) search and fuse the results with RRF. Falls back to…, _reciprocal_rank_fusion(), bm25_query() (+7 more)

### Community 4 - "prompts.py"
Cohesion: 0.29
Nodes (8): build_agentic_system_prompt(), build_rag_prompt(), Prompt templates for the RAG layer. Keeping them versioned in one place makes…, Returns (system_prompt, user_prompt) for the given prompt version and language., test_agentic_system_prompt_instructs_no_nested_llm_answer_de(), test_agentic_system_prompt_instructs_no_nested_llm_answer_en(), test_system_prompt_instructs_plain_text_answer_de(), test_system_prompt_instructs_plain_text_answer_en()

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

### Community 9 - "elasticsearch_client.py"
Cohesion: 0.09
Nodes (26): Path, main(), Utility script: indexes a small set of sample documents into Elasticsearch,…, download_and_extract(), load_corpus(), main(), Opt-in utility script: downloads the NFCorpus subset of the BEIR benchmark…, SentenceTransformer (+18 more)

### Community 10 - ".complete"
Cohesion: 0.40
Nodes (3): retry, Single non-streaming completion, with automatic retry on transient API errors., Multi-turn completion with optional tool-calling. Returns the raw response…

### Community 11 - "_test_env"
Cohesion: 0.50
Nodes (3): fixture, Ensure Settings() can be instantiated in tests without a real .env file., _test_env()

### Community 18 - "SearchRequest"
Cohesion: 0.14
Nodes (27): post, health(), get, search(), get_settings(), MCP server exposing this project's hybrid search as a tool for MCP clients…, Run hybrid (BM25 + kNN) search against the configured Elasticsearch index,…, search() (+19 more)

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
- **Why does `Settings` connect `Settings` to `index_routes.py`, `SearchRequest`, `elasticsearch_client.py`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `answer_search()` connect `SearchRequest` to `Settings`, `index_routes.py`, `hybrid_search.py`, `prompts.py`, `elasticsearch_client.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `SearchRequest` connect `SearchRequest` to `Settings`, `index_routes.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Settings` (e.g. with `LLMClient` and `_FailingLLMClient`) actually correct?**
  _`Settings` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `SearchRequest` (e.g. with `_FailingLLMClient` and `_ScriptedLLMClient`) actually correct?**
  _`SearchRequest` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `SearchResponse` (e.g. with `_FailingLLMClient` and `_ScriptedLLMClient`) actually correct?**
  _`SearchResponse` has 4 INFERRED edges - model-reasoned connections that need verification._