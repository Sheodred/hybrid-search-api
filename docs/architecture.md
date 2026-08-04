# Architecture

**Language:** **English** | [Deutsch](architecture.de.md)

```
Client
  |
  v
FastAPI (/search)
  |
  +--> Elasticsearch: BM25 search + kNN search -> Reciprocal Rank Fusion
  |
  +--> LLM (OpenAI-compatible endpoint): query understanding / RAG answer
        synthesis based on the top search results
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness of the API itself |
| GET | `/health/elasticsearch` | Elasticsearch cluster status |
| POST | `/search` | Hybrid search + optional RAG answer |
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
3. Optionally (`use_llm_answer=true` **and** at least one hit present), the
   top hits are passed as context to the configured LLM endpoint, which
   synthesizes a short, source-grounded answer (RAG pattern). The `lang`
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

## Adjustable search configuration

Two places are deliberately separated and independently editable:

- **`search/index_config.py`** - analyzers, filters (stemming, stopwords),
  and field mappings. This is where you switch to a different language,
  adjust the embedding dimension, or add synonyms.
- **`search/queries.py`** - the actual search query DSL (field boosts,
  fuzziness, size of the kNN candidate pool). This is where you tune *how*
  the search runs, independent of the fusion logic in `hybrid_search.py`.

This split mirrors the split in the prompts (`ai/prompts.py`):
configuration/template in one place, usage/orchestration in another.

## Why Reciprocal Rank Fusion?

RRF combines two ranked lists without having to manually weigh BM25 and
vector scores (which live on completely different scales) against each
other. That makes it a robust default choice for hybrid search.
