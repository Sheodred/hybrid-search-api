# Elasticsearch 8.14 -> 9.5.2 upgrade + modernization sweep

Status: approved, not yet implemented
Date: 2026-08-31
Follows: PR #18 (JSON snapshots, merged at `e8eab2d`)
Blocks: `docs/superpowers/specs/2026-08-31-rich-index-and-query-showcase-design.md`
(that spec assumes a modern Elasticsearch and currently carries an open
question about bumping the compose version - this lands first, on its own
branch, then that spec rebases on top)

## Context

The stack runs `docker.elastic.co/elasticsearch/elasticsearch:8.14.1`
(`docker-compose.yml`) with the Python client pinned `elasticsearch>=8.13,<9`
(`pyproject.toml`). The project is a portfolio piece for an Elasticsearch
specialist role; running the current major (the 9.5 line released
2026-08-04, `9.5.2` patch 2026-08-18) is a deliberate signal, and it clears
the path for the rich-index/query spec which wants a GA `retriever` API.

A full audit of every Elasticsearch call site was done during brainstorming.
**There is very little legacy to replace:**

| Check | Finding |
|---|---|
| `body=` parameter (removed in client 9.0) | Not used anywhere. `ensure_index` uses `settings=` / `mappings=`; `hybrid_search` / `index_routes` use `query=` / `knn=` / `from_=` / `size=`; seed scripts use `document=`. The 8.x kwargs migration is already done. |
| `Elasticsearch.__init__()` removed args (`timeout`, `maxsize`, `sniffer_timeout`, `sniff_on_connection_fail`, `randomize_hosts`, `host_info_callback`) | `build_client()` uses none - only `Elasticsearch(url)` or `Elasticsearch(url, api_key=...)`. |
| `elasticsearch_dsl` -> `elasticsearch.dsl` rename | N/A - the project builds raw query dicts, no DSL. |
| Client <-> server compatibility | The 9.x client is **not** compatible with ES 8.x (only 9.x / 10.x). So the client pin and the image bump must land together. |
| CI | `ci.yml` runs no Elasticsearch; all tests mock the client. The bump does not touch CI. |

The only genuine modernization target is `hybrid_search.py`: the top-level
`knn` search parameter plus the hand-rolled `_reciprocal_rank_fusion`, which
the native `rrf` retriever now replaces.

Brainstorming decisions:

- **Scope**: full modernization sweep - image + client pin + native `rrf`
  retriever + drop now-redundant mapping options + audit.
- **Order**: `feat/es9-upgrade` off `main` -> PR -> merge first. Then
  `feat/rich-index-query-showcase` rebases and is revised (see Coordination
  below).
- **Security**: `xpack.security.enabled=false` stays for the local dev /
  demo stack - same posture as today and `docs/architecture.md`. An ADR
  note records that production would enable it.
- **Implementation runs in a fresh session** off this spec plus a handoff
  doc.

## Goals

- Stack runs on `elasticsearch:9.5.2` with `elasticsearch>=9,<10`, all tests
  green, a clean local reseed, and a manual `/search` + `/health/elasticsearch`
  + `/index` smoke against the 9.5.2 container.
- `hybrid_search.py` uses the native `rrf` retriever instead of the
  top-level `knn` param + Python RRF, with behaviour equivalent to today
  (same two sub-queries, same result shape - no new request/response
  fields).
- Redundant `dense_vector` mapping options removed where 9.x makes them the
  default.
- Docs and the `CLAUDE.md` stack line reflect 9.x; an ADR records the
  upgrade.

## Non-goals

- **No behaviour or feature change.** No filters, facets, highlighting, new
  fields, or analyzer changes - all of that is the rich-index/query spec.
  This PR moves the platform and modernizes the implementation of what
  already exists.
- **German analyzer stays.** The English swap belongs to the other spec;
  touching it here would blur the boundary.
- No security hardening of the local stack.
- No CI change.
- No `docker-compose.yml` `local-llm` profile change.

## Approach

### 1. Platform bump

- `docker-compose.yml`: `image: docker.elastic.co/elasticsearch/elasticsearch:9.5.2`.
  `discovery.type=single-node`, `xpack.security.enabled=false`,
  `ES_JAVA_OPTS=-Xms512m -Xmx512m` unchanged. Verify at implementation time
  that `xpack.security.enabled=false` is still an accepted dev override in
  9.5 (it is expected to be).
- **esdata volume reset.** ES 9.x will not start on an 8.14-created data
  path (Elastic's N-1 rule). The data is throwaway demo content:
  `docker compose down -v` (or `docker volume rm hybrid-search-api_esdata`),
  then reseed. Confirm the exact volume name at implementation time - the
  compose project prefix has produced `hybrid-search-api_esdata` locally.
- `pyproject.toml`: `"elasticsearch>=8.13,<9"` -> `"elasticsearch>=9,<10"`.
- `CLAUDE.md`: the Stack line "Elasticsearch 8.x" -> "Elasticsearch 9.x".

### 2. ES-call audit + native retrieval

The audit result is in Context - only `hybrid_search.py` changes.

**`search/hybrid_search.py`**

- Replace the two-call BM25 + kNN + `_reciprocal_rank_fusion` path with a
  single `client.search` using the native `rrf` retriever:

  ```python
  resp = client.search(
      index=index,
      retriever={
          "rrf": {
              "retrievers": [
                  {"standard": {"query": bm25_query(query)}},
                  {"knn": {
                      "field": "embedding",
                      "query_vector": query_vector,
                      "k": size,
                      "num_candidates": size * KNN_CANDIDATE_MULTIPLIER,
                  }},
              ],
              "rank_constant": RRF_RANK_CONSTANT,
              "rank_window_size": size * KNN_CANDIDATE_MULTIPLIER,
          }
      },
      size=size,
      source_excludes=["embedding"],
  )
  ```

- The BM25-only fallback (no `query_vector`) stays a plain
  `client.search(index=index, query=bm25_query(query), size=size)`.
- `RRF_K` (currently in `hybrid_search.py`) becomes `RRF_RANK_CONSTANT` and
  moves to `queries.py` alongside `KNN_CANDIDATE_MULTIPLIER` (single home
  for tuning constants). **`knn_query()` needs no reshape** - its current
  output (`field` / `query_vector` / `k` / `num_candidates`) is exactly the
  body the `knn` sub-retriever takes, the same shape the old top-level
  `knn` param used. `hybrid_retriever(query, query_vector, size)` is a thin
  new builder in `queries.py` that assembles the `rrf` block from
  `bm25_query()` and `knn_query()`.
- **`_reciprocal_rank_fusion` and `tests/test_hybrid_search.py`'s
  `test_rrf_favors_docs_ranked_high_in_both_lists` are deleted** - that is
  the legacy implementation the native retriever replaces. Decided:
  delete, no `use_native_rrf` toggle. The RRF concept stays visible in
  `docs/search/` examples and ADR-0003. There is exactly one fusion path
  after this: the native retriever when a vector is present, plain BM25
  otherwise.
- `answering.py` / `_extract_score`: the native path puts the fused score
  in `_score` (no `_rrf_score`); `_extract_score` already falls back to
  `_score`, so no change. `answer_search` still gets a `list[dict]` of hits
  in the same shape.

### 3. Mapping touch-ups

**`search/index_config.py`** - `embedding` field:

- Drop `"index": true` - it is the default in 9.x, and float
  `dense_vector` fields are always indexed as `int8_hnsw` there.
- Keep `dims` and `similarity: cosine` explicit for readability. Confirm at
  implementation time whether `similarity` is still required or now
  defaults (be explicit regardless).
- No other mapping change. `EMBEDDING_DIMS = 384` stays; the German
  analyzer stays.

### 4. Tests + verification

- All tests mock the client -> they keep running. Adjust:
  - `tests/test_hybrid_search.py`: remove the deleted RRF-function test
    (unless the veto is taken); add/replace with a `Mock`-client assertion
    that the vector path calls `client.search` once with a `retriever=`
    kwarg and the no-vector path calls it with a `query=` kwarg.
  - `tests/test_queries.py`: `knn_query` is unchanged; add a small
    assertion for the new `hybrid_retriever()` builder (two sub-retrievers,
    one `standard` one `knn`, `rank_constant == RRF_RANK_CONSTANT`).
  - `tests/test_elasticsearch_client.py`, `tests/test_index_routes.py`:
    unchanged.
- Manual smoke against the 9.5.2 container (documented in the ADR / PR):
  1. `docker compose down -v && docker compose up -d elasticsearch`
  2. `python scripts/seed_data.py`
  3. `GET /health/elasticsearch` -> `status`, `number_of_nodes`
  4. `GET /index` -> mapping present, `document_count == 10`
  5. `POST /search {"query": "vector search", "use_llm_answer": false}` ->
     hits returned, ranking sane
- `/verify` (venv + tests + ruff) green.

### 5. Docs + ADR

- `docs/architecture.md` + `docs/architecture.de.md`: version mentions
  8.x -> 9.5.2; the flow diagram's "Reciprocal Rank Fusion" line ->
  "native `rrf` retriever".
- `README.md` + `README.de.md`: any ES version mention -> 9.5.2; keep both
  structurally identical.
- **New `docs/adr/0003-elasticsearch-9-upgrade.md`** (~30 lines): why 9.5.2
  now, that the client pin and image must move together, the esdata volume
  reset, the `knn` param + Python RRF -> native retriever swap, and that
  `xpack.security.enabled=false` is a deliberate local-dev choice.
- `CLAUDE.md`: stack line (see section 1). The "Known gotchas" reindex note
  already covers delete + reseed after mapping changes - no change needed
  there for this PR.

## Coordination with the rich-index/query spec

After `feat/es9-upgrade` merges, rebase `feat/rich-index-query-showcase` and
revise its spec:

- Section 3 / 4: the native `rrf` retriever already exists - those sections
  change from "introduce the retriever" to "extend the retriever's
  `standard` sub-query with `bool` / `filter`, and add `highlight` + `aggs`
  to the search call".
- Drop the `use_native_rrf` request-field toggle and the "Python RRF as
  fallback" framing entirely - `_reciprocal_rank_fusion` no longer exists
  after this PR.
- Delete the open question "pin against a newer compose version".
- Renumber that spec's planned ADR from `0003` to
  `0004-rich-index-and-query-showcase.md`.
- Section 3's mapping already planned to drop nothing from `embedding`;
  align it with the `index: true` removal done here.

## Deliberate simplifications (ponytail ledger)

- The esdata volume is destroyed rather than migrated (8.14 -> 8.18 -> 9.x).
  It is demo data reseeded from `scripts/seed_data.py` in seconds; a
  rolling upgrade would be pure ceremony here.
- `_reciprocal_rank_fusion` is deleted, not kept beside the native
  retriever - modernization means removing the replaced implementation. The
  RRF concept survives in `docs/search/` examples and the ADR.
- The native retriever is adopted with the current two simple sub-queries
  only. No filter/highlight/agg wiring - that is a separate spec.

## Open questions / deferred (resolve at implementation time, against live 9.5.2)

- Exact `dense_vector` mapping requirements in 9.5.2: is `similarity` still
  needed, does dropping `index: true` change anything for a 384-dim float
  vector. Be explicit regardless.
- `rrf` retriever licensing tier in 9.5.2 - expected to be free/basic
  (it moved off platinum in the 8.15 / 9.0 line); confirm against the
  running container, not from memory.
- `xpack.security.enabled=false` accepted as a dev override in the 9.5
  docker image (expected yes).
- Whether `rank_window_size` / `rank_constant` are the current key names in
  the 9.5.2 `rrf` retriever body (the 8.x `retriever` preview used
  `rank_window_size`; verify).
- Exact local esdata volume name (`hybrid-search-api_esdata` seen locally;
  depends on the compose project directory name).

## Implementation phases

1. `docker-compose.yml` image + esdata volume reset + `pyproject.toml`
   pin; bring the 9.5.2 container up locally, confirm it starts.
2. `hybrid_search.py` -> native `rrf` retriever; `queries.py` constant move
   + new `hybrid_retriever()` builder; update `tests/test_hybrid_search.py`
   (and `tests/test_queries.py` only if `knn_query` assertions need it);
   `/verify` green.
3. `index_config.py` `embedding` touch-up; `docker compose down -v` +
   reseed + manual smoke (`/health/elasticsearch`, `/index`, `/search`).
4. Docs (`architecture*.md`, `README*.md`, `CLAUDE.md`) + new
   `docs/adr/0003-elasticsearch-9-upgrade.md`.
5. PR, merge, then rebase + revise `feat/rich-index-query-showcase` per
   Coordination above.
