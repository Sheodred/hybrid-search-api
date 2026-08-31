# Rich index & query showcase

Status: approved, not yet implemented - **revised 2026-08-31 after the ES-9
upgrade**, see "Revision note" below
Date: 2026-08-31
Follows: PR #19 (Elasticsearch 9.5.2 upgrade, merged to `main` at `4ed8cdf`),
which in turn followed PR #18 (JSON snapshots of the index body / query DSL)

## Revision note (2026-08-31, after PR #19)

This spec was originally written against Elasticsearch 8.x and assumed the
native `rrf` retriever would be available after the upgrade. It is not:
verified against the running 9.5.2 container, the `rrf` and `linear`
retrievers are license-gated and return
`403 security_exception: current license is non-compliant` on a `basic`
license. Only the `standard` and `knn` retrievers are free, and neither
fuses anything - so the entire retriever API is off the table for this
project. See [ADR-0003](../../adr/0003-elasticsearch-9-upgrade.md).

Everything built on `retriever` has been re-planned onto the plain `_search`
API: `query` with `bool`/`filter`, top-level `knn`, `highlight` and `aggs`,
fused by the existing `_reciprocal_rank_fusion()`. Concretely this removed
the `hybrid_retriever()` builder, the `use_native_rrf` request field and its
dual code path, and `example_retriever_rrf.json`. **This makes the spec
smaller, not larger** - there is now one search path instead of two.

Also carried over from PR #19: the stack is on 9.5.2 with client
`elasticsearch>=9,<10`, and `"index": true` is already gone from the
`embedding` mapping.

## Context

The search core is wired end to end - `seed_data.py` embeds each document,
`answer_search()` embeds the query, `hybrid_search()` runs BM25 + kNN and
fuses them with a hand-rolled Python RRF, and the top hits feed a RAG
answer. The concept works. The depth does not match the project's framing
("Elasticsearch specialist" portfolio):

- **Index** = 3 fields (`title`, `content`, `embedding`), one custom
  analyzer - and that analyzer is **German** (`light_german`,
  `_german_` stopwords) while every seeded document, demo and NFCorpus, is
  **English**. No synonyms (the docstring promises them), no
  `search_analyzer`, no multi-fields, no metadata, no `copy_to`, no
  `dense_vector` tuning.
- **Documents** = `{title, content}`. `seed_nfcorpus.py` reads each BEIR
  row and discards everything but title and text.
- **Queries** = one `multi_match` (default `best_fields`) and one flat
  `knn`. No `bool`/`filter` context, no phrase matching, no aggregations,
  no highlighting. RRF is Python - and stays Python, since the native
  retriever is licensed (see the revision note).

This spec deliberately broadens the mapping and the query DSL so a reviewer
reading `search/index_config.py`, `search/queries.py`, and
`docs/search/*.json` can see the range of Elasticsearch concepts the author
works with. The added complexity is the requirement, not gold-plating -
but each concept must be real and exercised by a test, never decorative.

Decisions taken during brainstorming:

- **Dataset**: both. The demo set (10 docs) gains hand-authored metadata
  and drives CI; NFCorpus reuses the same mapping at ~3.6K-doc scale.
- **Scope**: focused - ~12 concepts that matter for hybrid search + RAG,
  not a 20-feature catalogue.
- **Wiring**: hybrid - filters, highlighting, and facets are wired into the
  running `/search` path (new request/response fields); the rest lives as
  reference JSON.
- **Validation**: shape + snapshots (no live Elasticsearch in CI). CI stays
  `pip install` + `ruff` + `pytest`. The live check is one documented
  command plus an optional helper script. GitHub is storage and
  documentation; there is no goal to run this online.

## Goals

- The index mapping demonstrates: index-vs-search analyzer split,
  `synonym_graph`, stemming / stopwords / possessive / `asciifolding`,
  `.keyword` and `.exact` multi-fields, `normalizer`, `term_vector` for
  highlighting, `dense_vector` with `int8_hnsw` quantization + HNSW params,
  `copy_to` catch-all, `index: false`, `dynamic: strict`, and
  `keyword` / `date` / `integer` fields for aggregation + filtering.
- The query DSL demonstrates: `bool` (must / should / filter),
  `most_fields` `multi_match`, `minimum_should_match`, `match_phrase` with
  `slop` on a `.exact` sub-field, a shared filter context, **kNN
  pre-filter**, the `unified` highlighter, `terms` / `date_histogram` /
  `stats` aggregations, `source_excludes`, and a `function_score`
  `gauss`-decay variant (reference-only).
- `/search` gains working `filters`, `facets`, `word_count_stats`, and
  per-hit `highlights` so the concepts are observable locally, not just on
  paper.
- Every builder's output is snapshotted to `docs/search/*.json` and
  asserted for structural invariants. Response-parsing logic (aggregations
  -> facets, highlight extraction) is unit-tested against hand-built ES
  response fixtures.
- `docs/search/README.md` explains, per example file, which concept it
  shows, which mapping field makes it work, and what to try changing.

## Non-goals

- No live Elasticsearch in CI. No `services:` container, no CI slowdown.
- Not a general search platform: no autocomplete / completion suggester,
  no `rank_features`, no percolator, no runtime fields, no `search_after` /
  `collapse` / `_explain` endpoints. Those are the "broad tour" that was
  explicitly declined.
- No new HTTP endpoints. `filters` / `facets` extend the existing
  `POST /search` contract additively.
- No change to `search/elasticsearch_client.py`, `search/embeddings.py`,
  `ai/llm_client.py`, `search/agentic_answering.py`, `main.py`, or `ci.yml`.
- Not re-running `graphify update .` as part of this change (it reverts the
  curated doc layer - see CLAUDE.md). The graph is left stale and that is
  noted in the PR / handoff.

## Approach

### 1. Index mapping - `search/index_config.py`

Replace the German analysis chain with English, and expand the mapping.
`build_index_body()` stays the Python source of truth; the snapshot test
regenerates `docs/search/index_settings.json` (PR #18 mechanism).

**`settings.analysis`**

```
filter:
  en_stop        { type: stop,    stopwords: _english_ }
  en_stemmer     { type: stemmer, language: light_english }
  en_possessive  { type: stemmer, language: possessive_english }
  domain_synonyms{ type: synonym_graph, synonyms: [
      "knn, k nearest neighbor, k-nearest-neighbor, ann, approximate nearest neighbor",
      "rag, retrieval augmented generation, retrieval-augmented generation",
      "bm25, okapi bm25, best match 25",
      "vector search, semantic search, dense retrieval, embedding search",
      "hnsw, hierarchical navigable small world",
      "nlp, natural language processing" ] }
analyzer:
  en_index  { tokenizer: standard,
              filter: [lowercase, en_possessive, en_stop, en_stemmer, asciifolding] }
  en_search { tokenizer: standard,
              filter: [lowercase, en_possessive, domain_synonyms, en_stop, en_stemmer, asciifolding] }
  exact     { tokenizer: standard, filter: [lowercase, asciifolding] }
normalizer:
  keyword_lower { type: custom, filter: [lowercase, asciifolding] }
```

`domain_synonyms` sits in the **search** analyzer only - keeps the index
small and lets the synonym list change without a full reindex (analyzer
reload still required). It is placed after `lowercase` / `en_possessive`
and before `en_stop` / `en_stemmer` so expansions are stopworded and
stemmed consistently.

**`mappings`** (`dynamic: "strict"`)

| Field | Type | Notes |
|---|---|---|
| `title` | `text`, `analyzer: en_index`, `search_analyzer: en_search` | `fields`: `keyword` (`keyword`, `ignore_above: 256`), `exact` (`text`, `analyzer: exact`) |
| `content` | `text`, `analyzer: en_index`, `search_analyzer: en_search`, `term_vector: with_positions_offsets` | `fields`: `exact` (`text`, `analyzer: exact`) |
| `all_text` | `text`, `analyzer: en_index`, `search_analyzer: en_search` | populated by `copy_to` from `title`, `content`, `tags` |
| `embedding` | `dense_vector`, `dims: 384`, `similarity: cosine` | `index_options: { type: int8_hnsw, m: 16, ef_construction: 100 }`. `index: true` is omitted - it is the 9.x default (dropped in PR #19). The explicit `index_options` is the point of the demo: without it 9.5.2 would pick `bbq_hnsw` at 384 dims, so this both shows the tuning knob and pins a stable value for the snapshot test. |
| `category` | `keyword`, `normalizer: keyword_lower` | terms agg + filter |
| `tags` | `keyword` (array), `normalizer: keyword_lower` | terms agg + filter; `copy_to: all_text` |
| `published` | `date`, `format: strict_date_optional_time\|\|epoch_millis` | `date_histogram` + range filter |
| `source` | `keyword` | filter |
| `url` | `keyword`, `index: false` | display / citation only, not searchable |
| `word_count` | `integer` | `stats` agg + range filter |

`EMBEDDING_DIMS = 384` stays and is asserted equal to
`mappings.properties.embedding.dims` by a test.

**Reindex is mandatory.** `ensure_index()` only creates a missing index, so
an existing `documents` index must be deleted and reseeded. Both seed
scripts must emit the new fields or `dynamic: strict` rejects the write.

### 2. Ingest & metadata

**`scripts/seed_data.py`** - each of the 10 `SAMPLE_DOCS` entries keeps
`title` / `content` and gains hand-authored `category`, `tags` (2-4),
`published`, `source`, `url`. Assignments:

| # | Doc | category | source |
|---|---|---|---|
| 1 | Elasticsearch Basics | fundamentals | handbook |
| 2 | Vector Search and Embeddings | vector-search | handbook |
| 3 | Retrieval-Augmented Generation (RAG) | rag | handbook |
| 4 | BM25 Ranking | lexical-search | handbook |
| 5 | Reciprocal Rank Fusion (RRF) | fusion | field-notes |
| 6 | ANN Search (HNSW) | vector-search | field-notes |
| 7 | Sentence Transformer Models | nlp | handbook |
| 8 | Full-Text vs. Semantic Search | fundamentals | handbook |
| 9 | Analyzers and Tokenization | lexical-search | field-notes |
| 10 | Prompt Engineering for RAG Systems | rag | field-notes |

- `published`: spread ~2023-06 to 2025-01 at roughly monthly gaps (feeds
  `date_histogram`).
- `url`: `https://kb.local/<title-slug>`.
- `word_count`: computed at seed time (`len(content.split())`), not
  hand-authored - stays correct if `content` is edited. Sent as an extra
  field alongside `embedding`.
- `all_text`: filled by ES via `copy_to`; nothing to send.
- 6 `category` values, 2 `source` values -> both terms facets have several
  buckets.
- New optional `--recreate` flag: `DELETE` the index before seeding, so the
  local check loop is one step shorter. `# ponytail: convenience flag, ~4 lines`

**`scripts/seed_nfcorpus.py`** - `load_corpus()` currently keeps only
`title` / `text`. Change to also carry:

- ES `_id` = the real `row["_id"]` (currently a running counter) - stable,
  traceable identifiers.
- `source: "nfcorpus"`, `category: "medical"` (constant, so the shared
  `category` facet stays valid), `word_count` computed.
- `url`: `row.get("url")` if present, else omit.
- `tags` from `row["metadata"]` (MeSH terms) **if the real `corpus.jsonl`
  carries them** - verify at implementation time, skip gracefully if not.
- `published`: not available -> omit. A missing *known* field is fine under
  `dynamic: strict`; only *unknown* fields are rejected.

Result: the demo index is fully populated (facet / filter demos); the
NFCorpus index is sparser but valid against the same mapping, proving it
holds at 3.6K docs.

### 3. Query DSL - `search/queries.py`

Constants: `TITLE_BOOST = 3`, `KNN_CANDIDATE_MULTIPLIER = 5`,
`PHRASE_BOOST = 2`, `PHRASE_SLOP = 2`, `MIN_SHOULD_MATCH = "75%"`,
`RRF_RANK_CONSTANT = 60` (moved here from `hybrid_search.RRF_K`, so the
constants have one home even though the fusion stays in Python).

| Builder | Returns / demonstrates |
|---|---|
| `text_query(query_text)` | `bool` with `must: [multi_match(type=most_fields, fields=[title^3, content, all_text], minimum_should_match="75%", fuzziness=AUTO)]` and `should: [match_phrase(content.exact, slop=2, boost=2)]`. No filters. |
| `filter_clauses(filters)` | Pure filter context shared by BM25 and kNN: `terms` (category / tags / source), `range` (published gte/lte, word_count gte/lte). Returns `[]` when `filters` is `None` or empty. |
| `bm25_query(query_text, filters=None)` | `text_query(query_text)` bool merged with `"filter": filter_clauses(filters)`. |
| `knn_query(query_vector, k, filters=None)` | `{ field: embedding, query_vector, k, num_candidates: k * KNN_CANDIDATE_MULTIPLIER, filter: { bool: { filter: filter_clauses(filters) } } }`. The filter is a **kNN pre-filter** - applied before the ANN search; `num_candidates` is drawn from the filtered set. |
| `highlight_config()` | `{ fields: { content: { type: unified, fragment_size: 150, number_of_fragments: 2, pre_tags: ["<em>"], post_tags: ["</em>"] } } }`. Uses the `term_vector` on `content`. |
| `facet_aggs()` | `{ categories: terms(category, size 20), tags: terms(tags, size 20), by_month: date_histogram(published, calendar_interval month, min_doc_count 1), word_count: stats(word_count) }`. |
| `recency_boosted_query(query_text)` | **Reference only, not called by the running search path.** `function_score` wrapping `bm25_query(query_text)` with a `gauss` decay on `published`. Docstring says so explicitly. Demonstrates score shaping / recency bias. |

### 4. Orchestration & API surface

**`search/hybrid_search.py`**

- `RRF_K` moves to `queries.RRF_RANK_CONSTANT` (single source).
  `_reciprocal_rank_fusion` stays - it is now the only fusion path, not a
  fallback.
- `@dataclass class HybridResult: hits: list[dict]; facets: dict[str, list[FacetBucket]]; word_count_stats: WordCountStats | None`
- `hybrid_search(client, index, query, query_vector=None, size=10, filters=None) -> HybridResult`
  - **BM25 call** (always made):
    `client.search(index=index, query=bm25_query(query, filters), size=size, highlight=highlight_config(), aggs=facet_aggs(), source_excludes=["embedding"])`.
  - **kNN call** (only when `query_vector is not None`):
    `client.search(index=index, knn=knn_query(query_vector, size, filters), size=size, source_excludes=["embedding"])`.
    No `highlight`/`aggs` here - see the two notes below.
  - Fuse with `_reciprocal_rank_fusion(bm25_hits, knn_hits)[:size]`, or
    return the BM25 hits directly when there is no vector.
  - `_parse_facets(aggregations) -> dict[str, list[FacetBucket]]` maps
    `categories` / `tags` / `by_month`; the `stats` agg is parsed
    separately into `WordCountStats`. Both are carried on `HybridResult`;
    `answering.py` copies them onto the `SearchResponse`.
- `source_excludes=["embedding"]` on every search call - the 384-float
  vector never appears in a response.

**Two consequences of fusing in Python that the spec must handle explicitly:**

1. **Aggregations ride on the BM25 call only.** Running them on both would
   double the work and produce two bucket sets to reconcile. ES computes
   aggregations over everything matching the query (not just the returned
   page), and both calls share the same filter context, so the counts are
   well-defined - but they describe *the BM25 match set under the active
   filters*, not the fused result set. State this in
   `docs/search/README.md`; it is a real distinction a reviewer may probe,
   and "the facets describe the lexical match set" is a defensible answer
   only if it is written down.

2. **`_reciprocal_rank_fusion` must not drop the `highlight` block.** Its
   current merge is `docs[doc_id] = hit` while walking each list in turn, so
   for a document present in *both* lists the kNN hit (no `highlight`, since
   only the BM25 call requests one) overwrites the BM25 hit that had it.
   Every doc ranking well on both sides - exactly the ones RRF promotes to
   the top - would silently lose its snippet. Fix by merging rather than
   replacing, keeping the first-seen (BM25) fields:
   `docs[doc_id] = {**hit, **docs.get(doc_id, {})}`, or by explicitly
   carrying `highlight` across. Needs its own unit test: a doc in both lists
   keeps its highlight.

   Documents that appear *only* in the kNN list legitimately have no
   snippet - `SearchHit.highlights` is `| None` and `answering.py` already
   falls back to full `content` for the RAG context.

**`models.py`**

```python
class SearchFilters(BaseModel):
    category: list[str] | None = None
    tags: list[str] | None = None
    source: list[str] | None = None
    published_after: date | None = None
    published_before: date | None = None
    min_word_count: int | None = None
    max_word_count: int | None = None
```

- `SearchRequest` gains `filters: SearchFilters | None = None`.
- `SearchHit` gains `highlights: list[str] | None = None`.
- `class FacetBucket(BaseModel): key: str | int; doc_count: int`
- `class WordCountStats(BaseModel): count: int; min: float | None; max: float | None; avg: float | None`
- `SearchResponse` gains `facets: dict[str, list[FacetBucket]] | None = None`
  and `word_count_stats: WordCountStats | None = None`.

**`search/answering.py`**

- Pass `request.filters` into `hybrid_search`; unpack `HybridResult` into
  hits + facets.
- Build each `SearchHit` with
  `highlights=hit.get("highlight", {}).get("content")`.
- `_extract_score` unchanged: it prefers `_rrf_score` (set by the fusion)
  and falls back to `_score` (the BM25-only path).
- RAG context: for each hit pass
  `content = " ... ".join(highlights) if highlights else full_content`
  to `build_rag_prompt` - shorter, focused context window
  ("passage-based RAG", fewer tokens).
- Return `facets` and `word_count_stats` in the `SearchResponse`.

**`api/routes.py`** - no logic change; `response_model` picks up the new
fields.

**`mcp_server.py`** - `search()` is checked at implementation time. If it
delegates to `answer_search`, it inherits `filters` for free. If it builds
its own request, add a `filters` passthrough or leave it minimal.

**`ai/prompts.py`** - `build_rag_prompt` already takes `list[dict]` with a
`content` key; no change needed since `answering.py` supplies the
snippet text as `content`. At most a one-line docstring note.

### 5. Reference JSON & tests

**`docs/search/*.json`** - rendered from the builders with one consistent
scenario: query `"approximate nearest neighbor search"`, `k = 10`,
`query_vector = [0.1, 0.2, 0.3]` (short placeholder), filters
`category=["vector-search"]`, `published_after="2024-01-01"`,
`min_word_count=40`.

| File | Source |
|---|---|
| `index_settings.json` | `build_index_body()` (auto-updated) |
| `example_search_request.json` | `SearchRequest(query=..., top_k=5, filters=SearchFilters(...))` (auto-updated) |
| `example_query_text.json` | `text_query(q)` |
| `example_query_bm25_filtered.json` | `bm25_query(q, filters)` |
| `example_query_knn_prefiltered.json` | `knn_query(vec, k, filters)` |
| `example_highlight.json` | `highlight_config()` |
| `example_aggs_facets.json` | `facet_aggs()` |
| `example_function_score_recency.json` | `recency_boosted_query(q)` |

PR #18's `example_query_bm25.json` / `example_query_knn.json` are replaced
by the filtered variants (not accumulated). The plain (`filters=None`) form
is described in `docs/search/README.md`.

**`tests/test_config_snapshots.py`** - keeps the PR #18 mechanism (render
-> compare -> rewrite + fail on drift). All 8 entries added, plus a few
cross-cutting invariants (mapping <-> analyzer split, `dynamic: strict`,
`int8_hnsw`, `url.index is False`).

**Structural-invariant tests** (in `test_queries.py` / `test_index_config.py`)
- these stand in for a live-ES check under the chosen validation approach:

- `text_query`: `bool.must` has a `multi_match`; `bool.should` has a
  `match_phrase` on `content.exact`.
- `bm25_query(q, filters)`: `bool.filter` contains a `terms` on `category`
  and a `range` on `published`.
- `knn_query(vec, k, filters)`: top-level `filter` present;
  `num_candidates == k * KNN_CANDIDATE_MULTIPLIER`.
- `facet_aggs()`: keys `{categories, tags, by_month, word_count}`;
  `by_month` is a `date_histogram`, `word_count` is `stats`.
- `filter_clauses(SearchFilters())` -> `[]`.
- `build_index_body()`: `content.analyzer != content.search_analyzer`;
  `embedding.index_options.type == "int8_hnsw"`;
  `mappings.dynamic == "strict"`; `url.index is False`;
  `embedding.dims == EMBEDDING_DIMS`.

**Unit tests (mocked ES, no cluster)**

- `test_hybrid_search.py`: a `Mock` client whose `.search()` returns a
  hand-built dict with `hits.hits` (2 docs, one carrying
  `highlight.content`) and `aggregations` (all four). Assert `hybrid_search`
  returns a `HybridResult` with parsed `facets` (FacetBucket lists),
  `word_count_stats`, and per-hit `highlights`. With a vector: two `.search`
  calls (one `query=`, one `knn=`) and the RRF ordering holds; without a
  vector: one `.search` call and the BM25 hits come back unfused. Plus the
  merge test from section 4: **a document present in both lists keeps the
  `highlight` block the BM25 call gave it.** The existing
  `test_rrf_favors_docs_ranked_high_in_both_lists` stays.
- `test_answering.py`: a stubbed `hybrid_search` returning hits with
  `highlights` -> the RAG prompt receives the joined snippet text as
  context, not the full `content`; `SearchResponse.facets` is populated.
  Existing `_FakeLLMClient` tests keep passing.
- `test_api.py`: the `answer_search` mock still works; one added case -
  a `filters` payload round-trips through the request model, and a
  malformed `published_after` yields 422.

**`scripts/run_examples.py`** (~20 lines) - POSTs every
`docs/search/example_query_*.json` to local Elasticsearch and prints hit
counts. Optional but it is the "inspect and learn locally" loop:

```
docker compose up -d elasticsearch
python scripts/seed_data.py --recreate
python scripts/run_examples.py
```

`# ponytail: helper script, not wired into tests/CI`

### 6. Docs

- **`docs/search/README.md`** (new) - per example file, 3-5 lines: which
  ES concept, which mapping field makes it work, what to try changing.
  Plus the manual runbook above and the plain-vs-filtered note.
- **`docs/architecture.md`** + **`docs/architecture.de.md`** - update the
  flow diagram (BM25 + kNN -> RRF, + highlight + facets in the response),
  the "Adjustable search configuration" section (new builders), the
  endpoints table (`/search` response now carries `facets`,
  `word_count_stats`, per-hit `highlights`), and the Embeddings section
  (`int8_hnsw` quantization). Add a short "what demonstrates what" table
  pointing at `docs/search/`. The RRF licensing paragraph added in PR #19
  stays as-is.
- **`README.md`** + **`README.de.md`** - feature list gains filters,
  facets, highlighting, structured metadata. Add the reindex note when
  pulling this change. Keep both READMEs structurally identical.
- **`docs/adr/0004-rich-index-and-query-showcase.md`** (new, ~30 lines;
  `0003` is taken by the ES-9 upgrade) -
  records *why* the mapping and queries are deliberately broader than a
  minimal service needs (portfolio / teaching), so a later reader or a
  `ponytail-audit` does not "simplify" it away.
- **`CLAUDE.md`** - extend the "Known gotchas" reindex note with
  `dynamic: strict` (unknown-field rejection) and the `--recreate` flag.
  One line.
- **`CONTEXT.md`** - only if it carries a glossary: add facet, filter
  context, pre-filter, reciprocal rank fusion, passage-based RAG. Check at
  implementation time.

## Concept coverage map

| Elasticsearch concept | Lives in | Shown by |
|---|---|---|
| Index vs. search analyzer split | `index_config.py` | `index_settings.json`, `docs/search/README.md` |
| `synonym_graph` (search-time) | `index_config.py` | `index_settings.json` |
| Stemming / stopwords / possessive / `asciifolding` | `index_config.py` | `index_settings.json` |
| `.keyword` / `.exact` multi-fields | `index_config.py` | `index_settings.json`, `example_query_text.json` |
| `normalizer` | `index_config.py` | `index_settings.json` |
| `term_vector` for highlighting | `index_config.py` | `example_highlight.json` |
| `dense_vector` + `int8_hnsw` + HNSW params | `index_config.py` | `index_settings.json` |
| `copy_to` catch-all | `index_config.py` | `index_settings.json` |
| `index: false` | `index_config.py` | `index_settings.json` |
| `dynamic: strict` | `index_config.py` | `index_settings.json`, seed-write behaviour |
| `bool` must / should / filter | `queries.py` | `example_query_bm25_filtered.json` |
| `most_fields` `multi_match`, `minimum_should_match` | `queries.py` | `example_query_text.json` |
| `match_phrase` + `slop` on `.exact` | `queries.py` | `example_query_text.json` |
| Shared filter context | `queries.py` | `example_query_bm25_filtered.json`, `example_query_knn_prefiltered.json` |
| kNN pre-filter | `queries.py` | `example_query_knn_prefiltered.json` |
| Reciprocal Rank Fusion (in-process; the native retriever is licensed) | `hybrid_search.py` | `_reciprocal_rank_fusion()` + its tests, [ADR-0003](../../adr/0003-elasticsearch-9-upgrade.md) |
| `unified` highlighter | `queries.py` | `example_highlight.json` |
| `terms` / `date_histogram` / `stats` aggregations | `queries.py` | `example_aggs_facets.json` |
| `source_excludes` | `hybrid_search.py` | code + `docs/search/README.md` |
| `function_score` `gauss` decay | `queries.py` (reference) | `example_function_score_recency.json` |

## Testing strategy

No live Elasticsearch. Three layers:

1. **Snapshot** - every builder rendered to `docs/search/*.json`; a stale
   file fails once, is rewritten, and gets committed (PR #18 mechanism).
2. **Structural invariants** - assertions on builder output shape that
   catch a builder producing valid-looking but wrong DSL (missing filter,
   wrong agg type, missing kNN pre-filter).
3. **Response parsing** - `hybrid_search`'s aggregation -> facet and
   highlight-extraction logic tested against hand-built ES response
   fixtures with a `Mock` client; both the native and fallback paths
   exercised.

Manual confirmation that Elasticsearch actually accepts the bodies is one
documented command (`scripts/run_examples.py` against a compose cluster).

## Deliberate simplifications (ponytail ledger)

- Aggregations are computed on the BM25 call only, so the facet counts
  describe the lexical match set under the active filters rather than the
  fused result set. Documented rather than engineered around; reconciling
  two bucket sets would cost more than the distinction is worth here.
- `all_text` in the `most_fields` query is partly redundant with
  `title` + `content`. Kept as the `copy_to` demo and a single-field
  fallback.
- `WordCountStats` is its own response field rather than folded into
  `facets` - cleaner typing, ~4 lines.
- `scripts/run_examples.py` and `seed_data.py --recreate` are convenience,
  not wired into tests or CI.
- NFCorpus documents are deliberately sparser than demo documents (no
  `published`, `tags` only if MeSH is present). Realistic, and it still
  validates the shared mapping at scale.

## Open questions / deferred

- Whether NFCorpus `corpus.jsonl` rows actually carry `url` / MeSH
  metadata - resolved by inspecting the real file during implementation;
  the loader degrades gracefully either way.
- `light_english` vs `english` (Porter) stemmer - `light_english` chosen to
  match the prior `light_german` choice and be less aggressive for search.
  Revisit only if recall suffers.
- ~~The native `rrf` retriever's exact request key names and any licence
  gate~~ - **resolved in PR #19: it is license-gated and unavailable on this
  stack.** See the revision note. This was the question that reshaped the
  spec; it should have been answered before the design was written, not
  deferred to implementation.
- `graphify update .` is not run. The graph goes stale for the touched
  files. If a later session needs it fresh, follow the backup/restore
  runbook in CLAUDE.md - do not run the bare update.

## Implementation phases

1. Mapping (`index_config.py`) + both seed scripts + local reindex.
2. `queries.py` builders + structural-invariant tests.
3. `hybrid_search.py` + `models.py` + `answering.py` + unit tests.
4. Snapshot test + `docs/search/*.json` + `run_examples.py`.
5. Docs + ADR 0004.
