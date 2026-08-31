# Architecture

**Language:** **English** | [Deutsch](architecture.de.md)

```
Client
  |
  v
FastAPI (/search)
  |
  +--> Elasticsearch: BM25 search (+ highlight + facet aggs)
  |                 + kNN search      -> Reciprocal Rank Fusion
  |    both narrowed by the same filter context
  |
  +--> LLM (OpenAI-compatible endpoint): query understanding / RAG answer
        synthesis based on the matching passages of the top results
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness of the API itself |
| GET | `/health/elasticsearch` | Elasticsearch cluster status |
| POST | `/search` | Hybrid search + optional RAG answer. Accepts `filters`; returns per-hit `highlights` plus `facets` and `word_count_stats` |
| GET | `/index` | Mapping and document count of the index |
| GET | `/index/documents` | Browse indexed documents (paginated, `limit`/`offset`) |

Deliberately without authentication (see the roadmap in the README) -
sufficient for a demo/portfolio instance; for real production use, at least
`/index*` would need protecting. If Elasticsearch itself is unreachable,
every endpoint (not just the index routes) returns a clear 502 instead of a
bare 500 - see the global exception handler in `main.py`.

## Request flow

1. The client sends a natural-language query to `POST /search`.
2. The search layer always runs a BM25 search; kNN search is added only when
   a query embedding is available (see the "Embeddings" section for the
   fallback). If both result lists are present, they are fused via
   Reciprocal Rank Fusion (RRF) - otherwise the BM25 ranking alone decides.
   Any `filters` on the request become a shared filter context applied to
   both halves - as a kNN **pre-filter** on the vector side, so the candidate
   pool is drawn from the filtered subset rather than trimmed afterwards.
3. Optionally (`use_llm_answer=true` **and** at least one hit present), the
   top hits are passed as context to the configured LLM endpoint, which
   synthesizes a short, source-grounded answer (RAG pattern). What gets
   passed is the *highlighted passages* rather than whole documents when
   highlighting matched something - fewer tokens, and the model's attention
   stays on the part that actually matched. The `lang`
   field (`"en"` default or `"de"`) controls both the language of this
   answer and the language of the error messages below. Errors from the LLM
   call (wrong key, unknown model, endpoint unreachable, ...) are passed
   through as meaningful 502 responses instead of a bare 500 - see
   `api/routes.py`.
4. The response, including the underlying hits, goes back to the client.

## Embeddings

Query and documents are embedded with a local `sentence-transformers` model
(`all-MiniLM-L6-v2`, 384 dimensions) - no external API call, no extra cost
per search. If loading the model fails, `/search` automatically falls back
to BM25-only search (see `api/routes.py`).

The vectors are stored with explicit `int8_hnsw` quantization: roughly a
quarter of the size of raw float32 at essentially unchanged recall. Stating it
explicitly also pins the behaviour - ES 9.x otherwise picks `bbq_hnsw` at 384
dimensions.

## Adjustable search configuration

Two places are deliberately separated and independently editable:

- **`search/index_config.py`** - analyzers, filters (stemming, stopwords),
  and field mappings. This is where you switch to a different language,
  adjust the embedding dimension, or add synonyms.
- **`search/queries.py`** - the actual search query DSL (field boosts,
  fuzziness, phrase slop, filter clauses, highlight config, facet
  aggregations, size of the kNN candidate pool). This is where you tune *how*
  the search runs, independent of the fusion logic in `hybrid_search.py`.

This split mirrors the split in the prompts (`ai/prompts.py`):
configuration/template in one place, usage/orchestration in another.

Both builders are rendered to JSON under [`docs/search/`](search/), one file
per concept, each with a short explanation of what it demonstrates, which
mapping field makes it work, and what to try changing.
`tests/test_config_snapshots.py` keeps those files in sync - edit the Python,
not the JSON. `python scripts/run_examples.py` runs every example against a
local cluster.

### What demonstrates what

| Concept | Where |
|---|---|
| Index vs. search analyzer split, `synonym_graph` | `index_config.py` -> `index_settings.json` |
| `.exact` / `.keyword` multi-fields, `normalizer` | `index_config.py` -> `index_settings.json` |
| `copy_to` catch-all, `index: false`, `dynamic: strict` | `index_config.py` -> `index_settings.json` |
| `dense_vector` + `int8_hnsw` + HNSW params | `index_config.py` -> `index_settings.json` |
| `bool` must/should/filter, `most_fields`, `match_phrase` + `slop` | `queries.py` -> `example_query_text.json` |
| Shared filter context | `queries.py` -> `example_query_bm25_filtered.json` |
| kNN pre-filter | `queries.py` -> `example_query_knn_prefiltered.json` |
| `unified` highlighter (+ passage-based RAG) | `queries.py` -> `example_highlight.json` |
| `terms` / `date_histogram` / `stats` aggregations | `queries.py` -> `example_aggs_facets.json` |
| `function_score` `gauss` decay (reference only) | `queries.py` -> `example_function_score_recency.json` |
| Reciprocal Rank Fusion, `source_excludes` | `hybrid_search.py` |

## Why Reciprocal Rank Fusion?

RRF combines two ranked lists without having to manually weigh BM25 and
vector scores (which live on completely different scales) against each
other. That makes it a robust default choice for hybrid search.

The fusion runs in `search/hybrid_search.py` rather than through
Elasticsearch's native `rrf` retriever, because that retriever is licensed
and returns a 403 on a `basic` license - see
[ADR-0003](adr/0003-elasticsearch-9-upgrade.md).
