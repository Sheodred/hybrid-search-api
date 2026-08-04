# Hybrid Search API

![CI](https://github.com/<user>/hybrid-search-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

Elasticsearch-Suche (klassisches BM25 **und** Vektor-/kNN-Suche, fusioniert per
Reciprocal Rank Fusion) kombiniert mit einer LLM-Schicht (Anthropic API), die aus
den Top-Treffern eine kurze, quellenbasierte Antwort formuliert (RAG-Pattern).

> Screenshot/Demo-GIF hier einfuegen, sobald die API laeuft.

## Warum dieses Projekt

Zeigt in einem zusammenhaengenden Projekt drei Kernkompetenzen:
- **Backend-Engineering** - sauber strukturierte FastAPI-Anwendung, getestet, containerisiert, CI.
- **Such-Spezialisierung** - Elasticsearch-Mapping, BM25, kNN-Vektorsuche, Ranking-Fusion.
- **KI-Integration** - produktionsnahe LLM-Anbindung (Retry-Logik, Streaming, versionierte Prompts, RAG).

## Architektur

Siehe [docs/architecture.md](docs/architecture.md).

## Setup

```bash
git clone <dein-repo-link>
cd hybrid-search-api
cp .env.example .env  # ANTHROPIC_API_KEY eintragen

docker compose up -d  # startet Elasticsearch + API

pip install -e ".[dev]"
python scripts/seed_data.py  # Beispieldaten indexieren
```

## Nutzung

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Wie funktioniert Vektorsuche?", "top_k": 5}'
```

Interaktive API-Doku (Swagger): http://localhost:8000/docs

## Tests

```bash
pytest -v
ruff check .
```

## Tech-Stack

Python 3.12 - FastAPI - Elasticsearch - Anthropic API - Docker - pytest - ruff - GitHub Actions

## Roadmap

- [x] Echtes Embedding-Modell fuer die Vektorsuche (sentence-transformers, all-MiniLM-L6-v2, lokal)
- [ ] Reranking der Top-Treffer mit einem Cross-Encoder
- [ ] Query-Caching
- [ ] Auth (API-Key) fuer den `/search`-Endpunkt

## Lizenz

MIT - siehe [LICENSE](LICENSE)
