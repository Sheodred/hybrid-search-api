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
- **AI integration** - production-style LLM integration (retry logic, streaming, versioned prompts, RAG), including a fully on-prem/data-sovereignty deployment mode for regulated environments (see below).

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

### Data-sovereignty deployment mode

The LLM client works against any OpenAI-compatible endpoint, which matters
for a real scenario: data that must never leave infrastructure you control
(GDPR, regulated industries). `docker compose --profile local-llm up` starts
a local [llama.cpp](https://github.com/ggml-org/llama.cpp) server alongside
Elasticsearch and the API - the RAG step then never makes an external call.
See [ADR-0002](docs/adr/0002-llama-server-for-data-sovereignty-deployments.md)
for why llama-server rather than the more familiar Ollama (short version:
Ollama doesn't enforce API-key auth by default, which would leave this
project's own auth-error handling silently untested against it).

```bash
docker compose --profile local-llm up -d   # also starts the local LLM server
```

```bash
# .env
LLM_API_KEY=local-dev-key
LLM_BASE_URL=http://localhost:8090/v1
LLM_MODEL=qwen2.5-1.5b
```

For casual local dev where data-sovereignty isn't the point, [Ollama](https://ollama.com)
is simpler to set up (see the commented-out block in `.env.example`). For
GPU-scale production self-hosting, the same `LLM_BASE_URL` swap works with
vLLM or TGI too - the app doesn't care which OpenAI-compatible server is on
the other end.

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

Set `"agentic": true` to let the LLM decide when/how to call search itself
(via this project's own MCP `search` tool, called in-process) instead of
running the fixed search-then-answer pipeline - useful for vague queries
that may need a refined follow-up search. Default is `false` (fixed
pipeline, as above). `use_llm_answer` does not apply in agentic mode - the
agentic loop always uses the LLM to decide and to answer.

Interactive API docs (Swagger): http://localhost:8000/docs

### MCP server

The same search is also exposed as an [MCP](https://modelcontextprotocol.io)
tool for MCP clients (Claude Desktop, Claude Code, etc.), as an addition
alongside the REST API - not a replacement. Add to your client's MCP config:

```json
{
  "mcpServers": {
    "hybrid-search-api": {
      "command": "python",
      "args": ["-m", "hybrid_search_api.mcp_server"],
      "cwd": "/path/to/hybrid-search-api"
    }
  }
}
```

Exposes one tool, `search(query, top_k=10, use_llm_answer=True, lang="en")`,
which wraps the same `answer_search()` logic the REST endpoint uses.

## Tests

```bash
pytest -v
ruff check .
```

## Tech stack

Python 3.11+ - FastAPI - Elasticsearch - OpenAI-compatible LLM integration - MCP - Docker - pytest - ruff - GitHub Actions

## Roadmap

- [x] Real embedding model for vector search (sentence-transformers, all-MiniLM-L6-v2, local)
- [ ] Reranking of top hits with a cross-encoder
- [ ] Query caching
- [ ] Auth (API key) for the `/search` endpoint

## License

MIT - see [LICENSE](LICENSE)
