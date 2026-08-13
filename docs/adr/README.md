# Architecture Decision Records — hybrid-search-api

Each ADR records a decision that will cost money or nerves later if reversed
carelessly. Format: Context, Decision, Options with a scoring table, Consequences.

| ADR | Decision | Status | Gist |
| --- | -------- | ------ | ---- |
| [0001](0001-local-embeddings-over-ollama.md) | Local sentence-transformers for embeddings, not Ollama | Accepted | No functional payoff at this corpus size; adds a required service to a "clone and `docker compose up`" demo |
| [0002](0002-llama-server-for-data-sovereignty-deployments.md) | llama-server (not Ollama) for the local/data-sovereignty LLM mode | Accepted | Ollama doesn't enforce API-key auth by default, silently defeating the error-handling this project showcases |

## Add a new ADR

Write one when a decision has at least two of these traits: hard to reverse,
touches more than one service, there was a serious alternative, or in six months
someone will ask "why did we do it this way". Never overwrite an existing ADR —
set its status to `Superseded by ADR-XXXX` and write a new one; the old reasoning
is the context the new decision makes sense in.
