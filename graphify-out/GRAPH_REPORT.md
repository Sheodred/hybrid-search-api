# Graph Report - C:\Users\adria\IdeaProjects\hybrid-search-api  (2026-08-12)

## Corpus Check
- 50 files · ~79,784 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 180 nodes · 293 edges · 18 communities (17 shown, 1 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 20 edges (avg confidence: 0.8)
- Token cost: 176,250 input · 0 output

## Community Hubs (Navigation)
- LLM Client & Prompts
- Settings, Seeding & Index Routes
- Architecture Docs & RRF Rationale
- Hybrid Search Core (BM25+kNN+RRF)
- Agent Session & Workflow Docs
- API Error Handling & Main App
- API Schema & Endpoints (Swagger)
- Embeddings Module
- Search API Tests
- Elasticsearch Index Config
- Hybrid Search Demo & RAG Answer
- Test Fixtures
- Project Root

## God Nodes (most connected - your core abstractions)
1. `Settings` - 16 edges
2. `search()` - 13 edges
3. `hybrid-search-api CLAUDE.md` - 13 edges
4. `Architecture (English)` - 13 edges
5. `build_client()` - 11 edges
6. `Swagger UI Screenshot` - 10 edges
7. `LLMClient` - 8 edges
8. `hybrid_search()` - 8 edges
9. `ensure_index()` - 7 edges
10. `list_documents()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `/verify Command` --semantically_similar_to--> `Contributing Guide`  [INFERRED] [semantically similar]
  .claude/commands/verify.md → CONTRIBUTING.md
- `CI GitHub Actions Workflow` --semantically_similar_to--> `Contributing Guide`  [INFERRED] [semantically similar]
  .github/workflows/ci.yml → CONTRIBUTING.md
- `RAG Grounding Example (README)` --semantically_similar_to--> `RAG Answer Synthesis Pattern`  [INFERRED] [semantically similar]
  README.md → docs/architecture.md
- `RAG Grounding Example (README, DE)` --semantically_similar_to--> `RAG Grounding Example (README)`  [INFERRED] [semantically similar]
  README.de.md → README.md
- `/rebuild Command` --references--> `hybrid-search-api CLAUDE.md`  [EXTRACTED]
  .claude/commands/rebuild.md → CLAUDE.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Local Verification Workflow (pytest + ruff)** — claude_commands_verify_verify_command, contributing_contributing_guide, github_workflows_ci_ci_workflow, pre_commit_config_pre_commit_hooks [INFERRED 0.85]
- **Agent Skills Documentation Set** — claude_project_instructions, docs_agents_domain_domain_docs_consumption, docs_agents_issue_tracker_issue_tracker_conventions, docs_agents_triage_labels_triage_label_mapping [EXTRACTED 1.00]
- **Session Startup Routine** — claude_commands_startup_startup_command, claude_graphify_workflow, claude_handoff_doc_workflow, docs_agents_issue_tracker_issue_tracker_conventions [EXTRACTED 1.00]

## Communities (18 total, 1 thin omitted)

### Community 0 - "LLM Client & Prompts"
Cohesion: 0.11
Nodes (24): BaseModel, post, retry, LLMClient, Thin wrapper around an OpenAI-compatible chat completions endpoint. Works…, Single non-streaming completion, with automatic retry on transient API errors., Yields text chunks as they arrive - use for a responsive, incremental UI., build_rag_prompt() (+16 more)

### Community 1 - "Settings, Seeding & Index Routes"
Cohesion: 0.16
Nodes (19): BaseSettings, main(), Utility script: indexes a small set of sample documents into Elasticsearch,…, elasticsearch_health(), index_info(), list_documents(), get, Introspection endpoints: Elasticsearch cluster health, index info, and a way to… (+11 more)

### Community 2 - "Architecture Docs & RRF Rationale"
Cohesion: 0.11
Nodes (22): ai/prompts.py, api/routes.py, /rebuild Command, Architecture (English), Architecture (German), Hybrid Search (BM25 + kNN + RRF) [DE], Reciprocal Rank Fusion (RRF) [DE], Why RRF Rationale [DE] (+14 more)

### Community 3 - "Hybrid Search Core (BM25+kNN+RRF)"
Cohesion: 0.18
Nodes (15): _bm25_search(), hybrid_search(), _knn_search(), Elasticsearch, Hybrid search: combines classic BM25 full-text search with kNN vector search…, Run BM25 (+ optionally kNN) search and fuse the results with RRF. Falls back to…, _reciprocal_rank_fusion(), bm25_query() (+7 more)

### Community 4 - "Agent Session & Workflow Docs"
Cohesion: 0.17
Nodes (16): /startup Command, /verify Command, Graphify Knowledge Graph Workflow, Handoff Document Workflow, hybrid-search-api CLAUDE.md, Ubiquitous Language Glossary, Contributing Guide, Docker Compose Services (+8 more)

### Community 5 - "API Error Handling & Main App"
Cohesion: 0.17
Nodes (14): ESConnectionError, exception_handler, JSONResponse, Request, es_connection_error_handler(), JSON response with an explicit charset for older HTTP clients., Applies to every route: if Elasticsearch itself is unreachable, return a clear…, UTF8JSONResponse (+6 more)

### Community 6 - "API Schema & Endpoints (Swagger)"
Cohesion: 0.27
Nodes (11): DocumentListResponse schema, DocumentPreview schema, ElasticsearchHealth schema, GET /health/elasticsearch endpoint, GET /health endpoint, HTTPValidationError schema, GET /index/documents endpoint, GET /index endpoint (+3 more)

### Community 7 - "Embeddings Module"
Cohesion: 0.27
Nodes (8): SentenceTransformer, embed_many(), _get_model(), Sentence-embedding helper for the kNN side of hybrid search. Uses a small local…, Batched embedding - more efficient than calling embed() in a loop., patch, test_embed_many_batches_multiple_texts(), test_embed_returns_list_of_floats()

### Community 8 - "Search API Tests"
Cohesion: 0.33
Nodes (8): patch, test_search_returns_502_on_bad_api_key(), test_search_returns_502_on_connection_error(), test_search_returns_502_on_rate_limit(), test_search_returns_502_on_unknown_model(), test_search_returns_502_when_elasticsearch_unreachable(), test_search_returns_german_error_when_lang_de(), test_search_without_llm_answer()

### Community 9 - "Elasticsearch Index Config"
Cohesion: 0.40
Nodes (4): build_index_body(), Elasticsearch index configuration: analyzers, filters, and field mappings. This…, Full index creation body: analysis settings + field mappings., test_build_index_body_has_settings_and_mappings()

### Community 10 - "Hybrid Search Demo & RAG Answer"
Cohesion: 0.67
Nodes (4): Hybrid Search (BM25 + kNN via RRF), RAG-style LLM Answer Feature, Swagger UI Search Demo (GIF), POST /search Endpoint

### Community 11 - "Test Fixtures"
Cohesion: 0.50
Nodes (3): fixture, Ensure Settings() can be instantiated in tests without a real .env file., _test_env()

## Ambiguous Edges - Review These
- `CI GitHub Actions Workflow` → `hybrid-search-api CLAUDE.md`  [AMBIGUOUS]
  .github/workflows/ci.yml · relation: conceptually_related_to

## Knowledge Gaps
- **16 isolated node(s):** `hybrid-search-api`, `Pre-commit Hooks Config`, `Serena Project Config`, `Ubiquitous Language Glossary`, `Docker Compose Services` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `CI GitHub Actions Workflow` and `hybrid-search-api CLAUDE.md`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Settings` connect `Settings, Seeding & Index Routes` to `LLM Client & Prompts`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `LLMClient` connect `LLM Client & Prompts` to `Settings, Seeding & Index Routes`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `hybrid-search-api CLAUDE.md` (e.g. with `Docker Compose Services` and `Serena Project Config`) actually correct?**
  _`hybrid-search-api CLAUDE.md` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `hybrid-search-api`, `Pre-commit Hooks Config`, `Serena Project Config` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `LLM Client & Prompts` be split into smaller, more focused modules?**
  _Cohesion score 0.10752688172043011 - nodes in this community are weakly interconnected._
- **Should `Architecture Docs & RRF Rationale` be split into smaller, more focused modules?**
  _Cohesion score 0.11255411255411256 - nodes in this community are weakly interconnected._