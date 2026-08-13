# ADR-0002: llama-server (not Ollama) for the local/data-sovereignty LLM deployment mode

## Context

The LLM client (`ai/llm_client.py`) already wraps any OpenAI-compatible
endpoint generically - `LLM_BASE_URL` + `LLM_API_KEY` + `LLM_MODEL`, no code
change needed per provider. That already covers local Ollama today, but only
as a documentation footnote (a paragraph and three env vars), not a runnable,
demonstrated deployment mode.

The case this needs to cover: a regulated-industry scenario (GDPR, e.g.
German insurance) where the LLM call must never leave infrastructure the
company controls - no cloud API calls permitted at all. That's a real,
recurring interview topic for this project's target roles, and "it's
technically possible if you set an env var" doesn't demonstrate it the way a
runnable `docker compose --profile local-llm up` does.

This decision is the mirror image of [ADR-0001](0001-local-embeddings-over-ollama.md):
that one rejected adding Ollama for *embeddings* because a zero-infra local
alternative (sentence-transformers) already existed with no payoff from
adding a service. Here, there is no in-process equivalent for chat
generation - a local LLM server is the only way to keep generation fully
on-prem, so the question is purely which server, not whether to add one.

## Decision

Add a docker-compose service running **llama.cpp's `llama-server`**
(`ghcr.io/ggml-org/llama.cpp:server`), gated behind a `local-llm` Compose
profile so it's opt-in and doesn't touch the default `docker compose up`
path. Document it as the recommended data-sovereignty deployment mode.
Ollama stays documented as a simpler alternative for casual local dev.

## Options considered

| Option | OpenAI-compat fidelity | Hardware fit | Verdict |
| --- | --- | --- | --- |
| **llama-server (chosen)** | Enforces real `--api-key` auth - a wrong key genuinely 401s, which the `openai` SDK correctly parses into `AuthenticationError` (verified directly against a running instance). Exercises the *exact* exception-mapping code in `api/routes.py` this project showcases as "production-style LLM integration." | CPU-first, GGUF/quantized, single small binary - fits "modest hardware, no GPU" | Selected |
| Ollama | Does **not** enforce API-key auth by default (accepts any/no key) - the `AuthenticationError` branch would be silently dead code against it. Not a bug, just a mismatch with what this demo needs to prove. | CPU-friendly, very easy setup, official image | Stays as the documented simple-local-dev alternative, not the data-sovereignty default |
| vLLM | Most spec-faithful OpenAI compat overall (built as an explicit drop-in) | Assumes a GPU and a multi-GB CUDA image - wrong fit for "runs on a laptop" | Named as the production/GPU-scale option, not defaulted to |
| text-generation-inference (TGI) | OpenAI-compat layer is the least mature of the candidates | GPU-oriented | Rejected |
| LocalAI | Fine, but a heavier reimplementation of what Ollama already does | Comparable to Ollama, no capability gain | Rejected - redundant with Ollama |

## Consequences

- `llm_client.py` needs no changes - the seam this ADR relies on is already there by design.
- The compose profile means the fast default path (bring your own cloud key) stays untouched; `docker compose --profile local-llm up` is the explicit opt-in for the fully air-gapped story.
- Revisit if: a GPU-backed demo environment becomes available (vLLM would then be worth defaulting to for the "production-grade" story), or llama-server's OpenAI-compat layer regresses.
