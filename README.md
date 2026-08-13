# Hybrid Search API

![CI](https://github.com/Sheodred/hybrid-search-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

**Language:** **English** | [Deutsch](README.de.md)

Elasticsearch search (classic BM25 **and** vector/kNN search, fused via
Reciprocal Rank Fusion) combined with an LLM layer (any OpenAI-compatible
endpoint - e.g. a company gateway in front of Claude, or OpenAI directly)
that turns the top hits into a short, source-grounded answer (RAG pattern).

![Search UI](docs/images/search-ui.jpg)

![Demo: searching via the built-in UI](docs/images/search-ui-demo.gif)

## Example (real output)

Request:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "How does vector search work?", "top_k": 3}'
```

`answer` field of the response:

> Based on the search results, vector search works by representing text as
> high-dimensional numeric vectors called embeddings. The key idea is that
> semantically similar content ends up positioned close together in this
> vector space, which allows the system to find related documents even when
> there is no exact word match between the query and the document.
>
> When performing a search, the system looks for vectors that are nearest to
> the query vector. According to the third result, Elasticsearch does this
> using an algorithm called HNSW (Hierarchical Navigable Small World), which
> finds similar vectors approximately but very efficiently. There is a
> tunable parameter called num_candidates that lets you control the
> trade-off between speed and accuracy.
>
> This approach is distinct from traditional full-text search, which relies
> on exact or fuzzy word matching. Vector search instead captures meaning
> and concept similarity, making it useful for finding conceptually related
> content that might use completely different wording.

The answer grounds specific claims in specific results (e.g. attributing
HNSW to "the third result") rather than presenting an unsourced, blended
summary - plain prose by design, so it reads naturally instead of dumping
Markdown headers and bullet lists into a JSON string.

Interactive API docs are also available via Swagger:

![Swagger UI](docs/images/swagger-ui.jpg)

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

Any OpenAI-compatible endpoint works for the LLM layer, including a local
model via [Ollama](https://ollama.com) - no cloud key required. Point
`LLM_BASE_URL` at Ollama's OpenAI-compatible endpoint instead of a cloud
gateway (see the commented-out block in `.env.example`):

```bash
LLM_API_KEY=ollama       # Ollama ignores the value, it just can't be empty
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.1
```

### Trying it against a larger, unrelated corpus

`seed_data.py`'s 10 sample docs are deliberately about search/RAG concepts
themselves, which makes for a clean demo but doesn't prove much about scale.
For that, `scripts/seed_nfcorpus.py` downloads
[NFCorpus](https://github.com/beir-cellar/beir) (~3.6K medical documents, a
recognized IR benchmark) into its own index, leaving the default one alone:

```bash
python scripts/seed_nfcorpus.py            # indexes into '<ELASTICSEARCH_INDEX>_nfcorpus'
ELASTICSEARCH_INDEX=documents_nfcorpus docker compose up -d --build api
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
