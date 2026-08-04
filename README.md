# Hybrid Search API

![CI](https://github.com/Sheodred/hybrid-search-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

**Language:** **English** | [Deutsch](README.de.md)

Elasticsearch search (classic BM25 **and** vector/kNN search, fused via
Reciprocal Rank Fusion) combined with an LLM layer (any OpenAI-compatible
endpoint - e.g. a company gateway in front of Claude, or OpenAI directly)
that turns the top hits into a short, source-grounded answer (RAG pattern).

![Swagger UI](docs/images/swagger-ui.jpg)

![Demo: POST /search via the Swagger UI](docs/images/swagger-search-demo.gif)

## Example (real output)

Request:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "How does vector search work?", "top_k": 3}'
```

`answer` field of the response:

> ## Vector Search
>
> According to **document [1]**, vector search works as follows:
>
> - Documents are represented as **embedding vectors**
> - The search uses **kNN (k-nearest-neighbor)** to find similar documents
> - Unlike classic search, **no exact word match** is required - instead,
>   **semantic similarity** is measured
>
> The other search results [2] and [3] cover related but different topics
> and don't provide further detail on vector search itself.

Notably, the model cites only the document that's actually relevant and
explicitly marks the other hits as not relevant, instead of blending them in
uncritically - that's the grounding behavior a RAG system is supposed to
deliver, not just claim to.

## Cost per RAG answer

Across 10 different, topically matched test queries (one per sample
document), the LLM answer step (`use_llm_answer=true`) averaged the
following token usage:

| Metric | Average |
|---|---|
| Prompt tokens (search context + question) | ~417 |
| Completion tokens (generated answer) | ~343 |
| Total | ~760 |

Deliberately given in tokens rather than euros/dollars: the actual cost
depends on the chosen LLM provider and its pricing - the token count is
independent of that and converts directly using the per-token price of
whichever model is in use.

## Why this project

Demonstrates three core competencies in one coherent project:
- **Backend engineering** - cleanly structured FastAPI application, tested, containerized, CI.
- **Search specialization** - Elasticsearch mapping, custom analyzers (stemming, stopwords), BM25, kNN vector search, ranking fusion.
- **AI integration** - production-style LLM integration (retry logic, streaming, versioned prompts, RAG).

## Architecture

See [docs/architecture.md](docs/architecture.md).

## Setup

```bash
git clone https://github.com/Sheodred/hybrid-search-api.git
cd hybrid-search-api
cp .env.example .env  # fill in LLM_API_KEY (+ LLM_BASE_URL if needed)

docker compose up -d  # starts Elasticsearch + API

pip install -e ".[dev]"
python scripts/seed_data.py  # indexes sample data - downloads the embedding
                              # model once on the very first run (~80MB)
```

## Usage

`POST /search` with `{"query": "...", "top_k": 5, "use_llm_answer": true, "lang": "en"}` -
`lang` is `"en"` (default) or `"de"` and controls the language of the RAG
answer as well as error messages. A real example including the answer is
shown above under "Example (real output)".

Interactive API docs (Swagger): http://localhost:8000/docs

## Tests

```bash
pytest -v
ruff check .
```

## Tech stack

Python 3.11+ - FastAPI - Elasticsearch - OpenAI-compatible LLM integration - Docker - pytest - ruff - GitHub Actions

## Roadmap

- [x] Real embedding model for vector search (sentence-transformers, all-MiniLM-L6-v2, local)
- [ ] Reranking of top hits with a cross-encoder
- [ ] Query caching
- [ ] Auth (API key) for the `/search` endpoint

## License

MIT - see [LICENSE](LICENSE)
