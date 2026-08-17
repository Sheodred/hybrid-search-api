# hybrid-search-api

Portfolio project for job applications (backend + AI integration +
Elasticsearch specialist). Elasticsearch hybrid search (BM25 + kNN via RRF)
combined with an LLM layer for RAG answers. See README.md and
docs/architecture.md for architecture/setup - please read before making
larger changes.

## Stack
- Python 3.11+ (tested locally on 3.14), FastAPI, Elasticsearch 8.x
- LLM via an OpenAI-compatible endpoint (LLM_* env vars in .env) - no direct
  Anthropic API call
- Docker Compose for Elasticsearch + API container
- Windows/PowerShell as the primary dev environment

## Known gotchas (please don't repeat)
- venv only applies per terminal session - check before every command
  whether `(.venv)` shows in the prompt, otherwise run
  `.\.venv\Scripts\Activate.ps1`.
- The Docker container does NOT pick up code changes automatically - after
  every change run `docker compose up -d --build api`, otherwise the old
  build keeps running unnoticed.
- After changes to `search/index_config.py` (analyzer/mapping), the ES index
  must be deleted and reseeded, otherwise the new mapping doesn't take
  effect:
  `Invoke-RestMethod -Method Delete -Uri http://localhost:9200/documents`
  then `python scripts/seed_data.py`.
- PowerShell: use `Invoke-RestMethod`, not curl syntax.
- Git author consistently "Adrian K. <92444350+Sheodred@users.noreply.github.com>".
- Before every `git push`: briefly check `git log --oneline -5` and
  `git status` to confirm the local history is really linear with the
  remote (there was once a divergence caused by parallel Copilot commits).

## Workflow
- New features/larger changes each go on their own branch (e.g. `feat/...`,
  `docs/...`) instead of committing directly to `main` - this keeps
  individual changes visible, reviewable/revertible, and independently
  mergeable. Branch off `main`, PR against `main`.

## Useful commands
- `/verify` - run tests + lint locally
- `/rebuild` - rebuild the Docker API container with the current code

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- **`graphify update .` reverts part of the curated doc layer - check before
  running it.** It re-extracts every file its structural extractor owns,
  including Markdown, and drops all nodes carrying that `source_file` first.
  The hand-curated concept nodes for `CONTEXT.md`, `.claude/commands/*.md`,
  the agentic-RAG plan/spec and `docs/agents/triage-labels.md` are replaced
  by heading-level nodes under different IDs, taking ~38 cross-file
  `rationale_for` / `references` edges and the 21 curated community names
  with them (308 nodes -> 307, 604 edges -> 577). It is not idempotent: this
  happens on *every* run, not only when something changed.
  It backs the curated graph up to `graphify-out/<YYYY-MM-DD>/` first
  (gitignored), so restore `graph.json`, `GRAPH_REPORT.md` and
  `manifest.json` from there, then re-run `graphify export html`.

## Agent skills

### Issue tracker

Issues and specs are tracked as GitHub issues in Sheodred/hybrid-search-api. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout — CONTEXT.md + docs/adr/ at the repo root. See `docs/agents/domain.md`.

### Triage labels

Maps the mattpocock-skills canonical triage roles to this repo's actual
issue-tracker label strings. See `docs/agents/triage-labels.md`.


## Starting a new session

Handoff documents (`/mattpocock-skills:handoff`) are never written into
this repo. They go to `C:\Users\<user>\.claude\handoff\hybrid-search-api\`,
one flat file per handoff named `<YYYY-MM-DD>T<HHMM>-<slug>.md` — e.g.
`2026-08-11T1830-custom-fields.md` (the slug names the topic only; the
project is already the folder). There's no auto-loading, a fresh session
only picks one up once told to read it, which `/startup` does.

At the start of a new session in this repo, run `/startup` — it covers
the graphify check, the agent-skills config check, and printing the
newest handoff doc for this repo from
`C:\Users\<user>\.claude\handoff\hybrid-search-api\`.
