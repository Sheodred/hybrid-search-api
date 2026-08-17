# Graph Report - .  (2026-08-17)

## Corpus Check
- 21 files · ~123,291 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 308 nodes · 604 edges · 21 communities (19 shown, 2 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 44 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Search Routing and Settings
- Index Introspection and Seeding
- App Bootstrap and Error Handling
- Architecture Decision Records
- Agentic RAG Plan and Spec
- Repo Conventions and Agent Docs
- Hybrid Search and RRF Fusion
- Embeddings and Corpus Loading
- Agentic Loop Tests
- Architecture Documentation
- Prompts and Agentic Loop
- LLM Client and Retry
- OpenAPI Surface
- Test Environment Fixtures
- Docker Compose Services
- Project Root

## God Nodes (most connected - your core abstractions)
1. `Settings` - 41 edges
2. `SearchRequest` - 32 edges
3. `answer_search()` - 30 edges
4. `LLMClient` - 16 edges
5. `SearchResponse` - 16 edges
6. `agentic_answer_search()` - 15 edges
7. `Agentic RAG via In-Process MCP Dogfooding` - 15 edges
8. `build_client()` - 13 edges
9. `SearchHit` - 12 edges
10. `Architecture (English)` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Three-Round Tool-Calling Loop` --semantically_similar_to--> `Opt-in agentic search mode: instead of the fixed embed -> search -> answer…`  [INFERRED] [semantically similar]
  docs/superpowers/specs/2026-08-17-agentic-rag-mcp-design.md → src/hybrid_search_api/search/agentic_answering.py
- `Search Answering (deep module)` --semantically_similar_to--> `Owns the /search request end to end: builds the ES client, embeds the query…`  [INFERRED] [semantically similar]
  CONTEXT.md → src/hybrid_search_api/search/answering.py
- `RAG Answer Token Cost` --conceptually_related_to--> `LLMClient`  [INFERRED]
  README.md → src/hybrid_search_api/ai/llm_client.py
- `elasticsearch Compose Service` --conceptually_related_to--> `build_client()`  [INFERRED]
  docker-compose.yml → src/hybrid_search_api/search/elasticsearch_client.py
- `Hybrid Search API (README, German)` --semantically_similar_to--> `Hybrid Search API (README)`  [INFERRED] [semantically similar]
  README.de.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Agentic RAG in-process MCP flow** — docs_superpowers_specs_2026_08_17_agentic_rag_mcp_design_in_memory_mcp_transport, docs_superpowers_specs_2026_08_17_agentic_rag_mcp_design_schema_discovery, docs_superpowers_specs_2026_08_17_agentic_rag_mcp_design_tool_calling_loop, src_hybrid_search_api_search_agentic_answering_agentic_answer_search, src_hybrid_search_api_mcp_server, src_hybrid_search_api_ai_llm_client_llmclient_complete_with_tools [EXTRACTED 1.00]
- **Data-sovereignty deployment story** — readme_data_sovereignty_mode, docs_adr_0002_llama_server_for_data_sovereignty_deployments_decision, docker_compose_local_llm_profile, src_hybrid_search_api_ai_llm_client_llmclient [EXTRACTED 1.00]
- **Dual-corpus demo surface** — readme_dataset_toggle, readme_nfcorpus_corpus, src_hybrid_search_api_static_index_dataset_toggle_control, docs_images_search_ui_demo_recording, src_hybrid_search_api_models_searchrequest [INFERRED 0.95]
- **Agent Skills Documentation Set** — claude_project_instructions, docs_agents_domain_domain_docs_consumption [EXTRACTED 1.00]

## Communities (21 total, 2 thin omitted)

### Community 0 - "Search Routing and Settings"
Cohesion: 0.13
Nodes (34): BaseSettings, In-Memory MCP Transport, post, Search Exposed as an MCP Tool, health(), get, search(), get_settings() (+26 more)

### Community 1 - "Index Introspection and Seeding"
Cohesion: 0.11
Nodes (26): /rebuild Command, BaseModel, api Compose Service, elasticsearch Compose Service, main(), Utility script: indexes a small set of sample documents into Elasticsearch,…, elasticsearch_health(), index_info() (+18 more)

### Community 2 - "App Bootstrap and Error Handling"
Cohesion: 0.09
Nodes (25): ESConnectionError, exception_handler, FileResponse, JSONResponse, Request, get, search_ui(), es_connection_error_handler() (+17 more)

### Community 3 - "Architecture Decision Records"
Cohesion: 0.09
Nodes (25): local-llm Compose Profile, ADR-0001: Local sentence-transformers for embeddings, not Ollama, Consequences, Context, ADR-0001: Local sentence-transformers, not Ollama, Options considered, ADR-0002: llama-server (not Ollama) for the local/data-sovereignty LLM deployment mode, Consequences (+17 more)

### Community 4 - "Agentic RAG Plan and Spec"
Cohesion: 0.08
Nodes (24): Global Constraints, Agentic RAG Implementation Plan, Task 1: Add `anyio` as an explicit dependency, Task 2: Add `agentic` field to `SearchRequest`, Task 3: Add `LLMClient.complete_with_tools()`, Task 4: Add agentic system prompt, Task 5: `search/agentic_answering.py` - the tool-calling loop, Task 6: Wire `answer_search()` to branch on `request.agentic` (+16 more)

### Community 5 - "Repo Conventions and Agent Docs"
Cohesion: 0.10
Nodes (25): /startup Command, /verify Command, CI Pipeline (lint + test), Ruff Pre-commit Hooks, Graphify Knowledge Graph Workflow, Handoff Document Workflow, hybrid-search-api CLAUDE.md, Search Answering (deep module) (+17 more)

### Community 6 - "Hybrid Search and RRF Fusion"
Cohesion: 0.18
Nodes (15): _bm25_search(), hybrid_search(), _knn_search(), Elasticsearch, Hybrid search: combines classic BM25 full-text search with kNN vector search…, Run BM25 (+ optionally kNN) search and fuse the results with RRF. Falls back to…, _reciprocal_rank_fusion(), bm25_query() (+7 more)

### Community 7 - "Embeddings and Corpus Loading"
Cohesion: 0.17
Nodes (15): Path, download_and_extract(), load_corpus(), main(), Opt-in utility script: downloads the NFCorpus subset of the BEIR benchmark…, SentenceTransformer, embed(), embed_many() (+7 more)

### Community 8 - "Agentic Loop Tests"
Cohesion: 0.30
Nodes (14): SimpleNamespace, SearchHit, SearchResponse, agentic_answer_search(), _FailingLLMClient, _message(), patch, _ScriptedLLMClient (+6 more)

### Community 9 - "Architecture Documentation"
Cohesion: 0.14
Nodes (16): ai/prompts.py, api/routes.py, Architecture (English), Architecture (German), Hybrid Search (BM25 + kNN + RRF) [DE], Reciprocal Rank Fusion (RRF) [DE], Why RRF Rationale [DE], sentence-transformers all-MiniLM-L6-v2 Embeddings (+8 more)

### Community 10 - "Prompts and Agentic Loop"
Cohesion: 0.20
Nodes (12): ClientSession, build_agentic_system_prompt(), build_rag_prompt(), Prompt templates for the RAG layer. Keeping them versioned in one place makes…, Returns (system_prompt, user_prompt) for the given prompt version and language., _assistant_message_from(), _execute_tool_call(), _run_agentic_loop() (+4 more)

### Community 11 - "LLM Client and Retry"
Cohesion: 0.21
Nodes (9): retry, LLMClient, Thin wrapper around an OpenAI-compatible chat completions endpoint. Works…, Single non-streaming completion, with automatic retry on transient API errors., Multi-turn completion with optional tool-calling. Returns the raw response…, patch, test_complete_returns_text_from_response(), test_complete_with_tools_omits_tools_kwarg_when_none() (+1 more)

### Community 12 - "OpenAPI Surface"
Cohesion: 0.27
Nodes (11): DocumentListResponse schema, DocumentPreview schema, ElasticsearchHealth schema, GET /health/elasticsearch endpoint, GET /health endpoint, HTTPValidationError schema, GET /index/documents endpoint, GET /index endpoint (+3 more)

### Community 13 - "Test Environment Fixtures"
Cohesion: 0.50
Nodes (3): fixture, Ensure Settings() can be instantiated in tests without a real .env file., _test_env()

## Knowledge Gaps
- **44 isolated node(s):** `hybrid-search-api`, `RAG Answer Synthesis Pattern`, `sentence-transformers all-MiniLM-L6-v2 Embeddings`, `Graphify Knowledge Graph Workflow`, `Handoff Document Workflow` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `answer_search()` connect `Search Routing and Settings` to `Index Introspection and Seeding`, `Agentic RAG Plan and Spec`, `Repo Conventions and Agent Docs`, `Hybrid Search and RRF Fusion`, `Embeddings and Corpus Loading`, `Agentic Loop Tests`, `Prompts and Agentic Loop`, `LLM Client and Retry`?**
  _High betweenness centrality (0.279) - this node is a cross-community bridge._
- **Why does `Search Answering (deep module)` connect `Repo Conventions and Agent Docs` to `Search Routing and Settings`?**
  _High betweenness centrality (0.180) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Settings` (e.g. with `LLMClient` and `_FailingLLMClient`) actually correct?**
  _`Settings` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `SearchRequest` (e.g. with `Built-in Search UI` and `_FailingLLMClient`) actually correct?**
  _`SearchRequest` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `LLMClient` (e.g. with `RAG Answer Token Cost` and `Settings`) actually correct?**
  _`LLMClient` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `SearchResponse` (e.g. with `_FailingLLMClient` and `_ScriptedLLMClient`) actually correct?**
  _`SearchResponse` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `hybrid-search-api`, `RAG Answer Synthesis Pattern`, `sentence-transformers all-MiniLM-L6-v2 Embeddings` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._