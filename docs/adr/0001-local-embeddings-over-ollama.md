# ADR-0001: Local sentence-transformers for embeddings, not Ollama

## Context

The kNN side of hybrid search needs a query/document embedding model. The LLM
*generation* step (`ai/llm_client.py`) already supports any OpenAI-compatible
endpoint, including a local Ollama server, purely via `LLM_BASE_URL` — no code
change needed. It's fair to ask whether the *embedding* step (`search/embeddings.py`)
should follow the same pattern and call Ollama's embedding API (e.g.
`nomic-embed-text`) instead of running a model in-process.

## Decision

Keep embeddings local via `sentence-transformers` (`all-MiniLM-L6-v2`, 384 dims).
Do not add Ollama as an embeddings backend.

## Options considered

| Option | Runtime deps | Setup | Reversibility | Fit with project pitch |
| --- | --- | --- | --- | --- |
| **sentence-transformers (current)** | None beyond the Python package; model cached locally after first run | `docker compose up`, nothing else | N/A (status quo) | Matches "clone, `docker compose up`, done" |
| Ollama embeddings | A running Ollama server, a pulled embedding model | Install Ollama, pull model, keep it running | Hard — different model means a different vector dimensionality, forcing an index delete + reseed | Adds a service the demo depends on being up and warmed, with no functional payoff at this corpus size |

## Consequences

- `search/embeddings.py`'s `MODEL_NAME` stays hardcoded (no config seam for swapping models) — that's a deliberate simplicity choice, not an oversight. If a real second embeddings backend is ever needed, that's when the seam gets built (and this ADR should be revisited, not silently overridden).
- The LLM-client precedent (config-only provider swap) does **not** generalize to embeddings: `llm_client.py`'s seam exists because the OpenAI SDK's client already abstracts the endpoint; `embeddings.py` has no equivalent abstraction, and building one purely to enable an Ollama option would be speculative — nothing today calls for it.
- Revisit this if: the demo corpus grows enough that embedding latency matters, or there's a concrete reason to demonstrate a swappable embeddings seam (distinct from the LLM one already shown).
