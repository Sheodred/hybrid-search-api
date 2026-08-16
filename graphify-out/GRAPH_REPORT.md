# Graph Report - hybrid-search-api  (2026-08-17)

## Corpus Check
- 54 files · ~37,170 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 227 nodes · 412 edges · 19 communities (18 shown, 1 thin omitted)
- Extraction: 94% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 22 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f0dc9309`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- LLMClient
- index_routes.py
- Architecture (English)
- hybrid_search.py
- hybrid-search-api CLAUDE.md
- main.py
- Swagger UI Screenshot
- ADR-0001: Local sentence-transformers for embeddings, not Ollama
- test_api.py
- config.py
- _test_env
- hybrid-search-api
- Settings
- build_rag_prompt

## God Nodes (most connected - your core abstractions)
1. `Settings` - 27 edges
2. `answer_search()` - 23 edges
3. `SearchRequest` - 17 edges
4. `hybrid-search-api CLAUDE.md` - 13 edges
5. `Architecture (English)` - 13 edges
6. `build_client()` - 12 edges
7. `_FakeLLMClient` - 10 edges
8. `Swagger UI Screenshot` - 10 edges
9. `LLMClient` - 8 edges
10. `get_settings()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `/verify Command` --semantically_similar_to--> `Contributing Guide`  [INFERRED] [semantically similar]
  .claude/commands/verify.md → CONTRIBUTING.md
- `CI GitHub Actions Workflow` --semantically_similar_to--> `Contributing Guide`  [INFERRED] [semantically similar]
  .github/workflows/ci.yml → CONTRIBUTING.md
- `RAG Grounding Example (README)` --semantically_similar_to--> `RAG Answer Synthesis Pattern`  [INFERRED] [semantically similar]
  README.md → docs/architecture.md
- `RAG Grounding Example (README, DE)` --semantically_similar_to--> `RAG Grounding Example (README)`  [INFERRED] [semantically similar]
  README.de.md → README.md
- `test_search_tool_builds_request_and_returns_dict()` --calls--> `SearchHit`  [INFERRED]
  tests/test_mcp_server.py → src/hybrid_search_api/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Local Verification Workflow (pytest + ruff)** — claude_commands_verify_verify_command, contributing_contributing_guide, github_workflows_ci_ci_workflow, pre_commit_config_pre_commit_hooks [INFERRED 0.85]
- **Agent Skills Documentation Set** — claude_project_instructions, docs_agents_domain_domain_docs_consumption, docs_agents_issue_tracker_issue_tracker_conventions, docs_agents_triage_labels_triage_label_mapping [EXTRACTED 1.00]
- **Session Startup Routine** — claude_commands_startup_startup_command, claude_graphify_workflow, claude_handoff_doc_workflow, docs_agents_issue_tracker_issue_tracker_conventions [EXTRACTED 1.00]

## Communities (19 total, 1 thin omitted)

### Community 0 - "LLMClient"
Cohesion: 0.18
Nodes (7): retry, LLMClient, Thin wrapper around an OpenAI-compatible chat completions endpoint. Works…, Single non-streaming completion, with automatic retry on transient API errors., Yields text chunks as they arrive - use for a responsive, incremental UI., patch, test_complete_returns_text_from_response()

### Community 1 - "index_routes.py"
Cohesion: 0.30
Nodes (13): BaseModel, elasticsearch_health(), index_info(), list_documents(), get, Introspection endpoints: Elasticsearch cluster health, index info, and a way to…, DocumentListResponse, DocumentPreview (+5 more)

### Community 2 - "Architecture (English)"
Cohesion: 0.11
Nodes (22): ai/prompts.py, api/routes.py, /rebuild Command, Architecture (English), Architecture (German), Hybrid Search (BM25 + kNN + RRF) [DE], Reciprocal Rank Fusion (RRF) [DE], Why RRF Rationale [DE] (+14 more)

### Community 3 - "hybrid_search.py"
Cohesion: 0.18
Nodes (15): _bm25_search(), hybrid_search(), _knn_search(), Elasticsearch, Hybrid search: combines classic BM25 full-text search with kNN vector search…, Run BM25 (+ optionally kNN) search and fuse the results with RRF. Falls back to…, _reciprocal_rank_fusion(), bm25_query() (+7 more)

### Community 4 - "hybrid-search-api CLAUDE.md"
Cohesion: 0.17
Nodes (16): /startup Command, /verify Command, Graphify Knowledge Graph Workflow, Handoff Document Workflow, hybrid-search-api CLAUDE.md, Ubiquitous Language Glossary, Contributing Guide, Docker Compose Services (+8 more)

### Community 5 - "main.py"
Cohesion: 0.12
Nodes (17): ESConnectionError, exception_handler, FileResponse, JSONResponse, Request, get, search_ui(), es_connection_error_handler() (+9 more)

### Community 6 - "Swagger UI Screenshot"
Cohesion: 0.27
Nodes (11): DocumentListResponse schema, DocumentPreview schema, ElasticsearchHealth schema, GET /health/elasticsearch endpoint, GET /health endpoint, HTTPValidationError schema, GET /index/documents endpoint, GET /index endpoint (+3 more)

### Community 7 - "ADR-0001: Local sentence-transformers for embeddings, not Ollama"
Cohesion: 0.17
Nodes (10): ADR-0001: Local sentence-transformers for embeddings, not Ollama, Consequences, Context, Decision, Options considered, ADR-0002: llama-server (not Ollama) for the local/data-sovereignty LLM deployment mode, Consequences, Context (+2 more)

### Community 8 - "test_api.py"
Cohesion: 0.33
Nodes (8): patch, test_search_returns_200_with_hits(), test_search_returns_502_on_bad_api_key(), test_search_returns_502_on_connection_error(), test_search_returns_502_on_rate_limit(), test_search_returns_502_on_unknown_model(), test_search_returns_502_when_elasticsearch_unreachable(), test_search_returns_german_error_when_lang_de()

### Community 9 - "config.py"
Cohesion: 0.07
Nodes (33): Path, main(), Utility script: indexes a small set of sample documents into Elasticsearch,…, download_and_extract(), load_corpus(), main(), Opt-in utility script: downloads the NFCorpus subset of the BEIR benchmark…, SentenceTransformer (+25 more)

### Community 11 - "_test_env"
Cohesion: 0.50
Nodes (3): fixture, Ensure Settings() can be instantiated in tests without a real .env file., _test_env()

### Community 18 - "Settings"
Cohesion: 0.22
Nodes (22): BaseSettings, post, health(), get, search(), Central application configuration, populated from environment variables / .env., Settings, SearchRequest (+14 more)

### Community 19 - "build_rag_prompt"
Cohesion: 0.38
Nodes (5): build_rag_prompt(), Prompt templates for the RAG layer. Keeping them versioned in one place makes…, Returns (system_prompt, user_prompt) for the given prompt version and language., test_system_prompt_instructs_plain_text_answer_de(), test_system_prompt_instructs_plain_text_answer_en()

## Ambiguous Edges - Review These
- `CI GitHub Actions Workflow` → `hybrid-search-api CLAUDE.md`  [AMBIGUOUS]
  .github/workflows/ci.yml · relation: conceptually_related_to

## Knowledge Gaps
- **23 isolated node(s):** `hybrid-search-api`, `Context`, `Decision`, `Options considered`, `Consequences` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `CI GitHub Actions Workflow` and `hybrid-search-api CLAUDE.md`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Settings` connect `Settings` to `LLMClient`, `index_routes.py`, `config.py`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `answer_search()` connect `Settings` to `LLMClient`, `index_routes.py`, `hybrid_search.py`, `config.py`, `build_rag_prompt`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `LLMClient` connect `LLMClient` to `Settings`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Settings` (e.g. with `LLMClient` and `_FakeLLMClient`) actually correct?**
  _`Settings` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `hybrid-search-api CLAUDE.md` (e.g. with `Docker Compose Services` and `Serena Project Config`) actually correct?**
  _`hybrid-search-api CLAUDE.md` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `hybrid-search-api`, `Context`, `Decision` to the rest of the system?**
  _23 weakly-connected nodes found - possible documentation gaps or missing edges._