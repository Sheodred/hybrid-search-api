# Hybrid Search API

![CI](https://github.com/Sheodred/hybrid-search-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

**Sprache:** [English](README.md) | **Deutsch**

Elasticsearch-Suche (klassisches BM25 **und** Vektor-/kNN-Suche, fusioniert per
Reciprocal Rank Fusion) kombiniert mit einer LLM-Schicht (jeder OpenAI-kompatible
Endpunkt - z. B. ein Firmen-Gateway vor Claude, oder OpenAI direkt), die aus
den Top-Treffern eine kurze, quellenbasierte Antwort formuliert (RAG-Pattern).

![Such-UI](docs/images/search-ui.jpg)

![Demo: Suche ueber die eingebaute UI](docs/images/search-ui-demo.gif)

## Beispiel (echter Output)

Anfrage:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Wie funktioniert Vektorsuche?", "top_k": 3, "lang": "de"}'
```

`answer`-Feld der Antwort:

> Zur Vektorsuche liefern die Suchergebnisse nur begrenzte, aber relevante
> Informationen. Grundlage der Vektorsuche sind sogenannte
> Embedding-Vektoren. Laut Dokument "Sentence Transformer Models" wandeln
> Modelle wie all-MiniLM-L6-v2 ganze Saetze in solche Vektoren um, anstatt
> einzelne Woerter isoliert zu betrachten. Dadurch koennen Kontext und
> Bedeutung besser erfasst werden als mit klassischen Wort-Embeddings. Die
> eigentliche Suche funktioniert dann so, dass Suchanfragen ebenfalls in
> einen Vektor umgewandelt und mit den gespeicherten Vektoren verglichen
> werden, um semantisch aehnliche Inhalte zu finden. Wie genau dieser
> Vergleich technisch ablaeuft, etwa durch Aehnlichkeitsmasse wie
> Kosinus-Aehnlichkeit, geht aus den vorliegenden Suchergebnissen jedoch
> nicht hervor. Darueber hinaus enthalten die anderen Dokumente keine
> weiteren Informationen zur Vektorsuche.

Bemerkenswert: Das Modell benennt explizit, was die Quellen *nicht*
hergeben (die technische Funktionsweise des Vektorvergleichs), statt sich
etwas auszudenken - genau das Grounding-Verhalten, das ein RAG-System
liefern soll, nicht nur behauptet.

Interaktive API-Dokumentation ist ebenfalls per Swagger verfuegbar:

![Swagger UI](docs/images/swagger-ui.jpg)

## Kosten pro RAG-Antwort

Ueber 10 unterschiedliche, inhaltlich passende Testanfragen (eine pro
Beispieldokument) ergab sich im Schnitt folgender Tokenverbrauch fuer den
LLM-Antwortschritt (`use_llm_answer=true`):

| Metrik | Durchschnitt |
|---|---|
| Prompt-Tokens (Suchkontext + Frage) | ~417 |
| Completion-Tokens (generierte Antwort) | ~343 |
| Gesamt | ~760 |

Bewusst in Tokens statt in Euro/Dollar angegeben: Der tatsaechliche
Geldbetrag haengt vom gewaehlten LLM-Provider und dessen Preisliste ab -
die Tokenzahl bleibt davon unabhaengig und laesst sich mit dem Preis pro
Token des jeweils eingesetzten Modells direkt umrechnen.

## Warum dieses Projekt

Zeigt in einem zusammenhaengenden Projekt drei Kernkompetenzen:
- **Backend-Engineering** - sauber strukturierte FastAPI-Anwendung, getestet, containerisiert, CI.
- **Such-Spezialisierung** - Elasticsearch-Mapping, custom Analyzer (Stemming, Stoppwoerter), BM25, kNN-Vektorsuche, Ranking-Fusion.
- **KI-Integration** - produktionsnahe LLM-Anbindung (Retry-Logik, Streaming, versionierte Prompts, RAG), inklusive vollstaendig on-prem betreibbarem Datenschutz-Modus fuer regulierte Umgebungen (siehe unten).

## Architektur

Siehe [docs/architecture.de.md](docs/architecture.de.md).

## Setup

```bash
git clone https://github.com/Sheodred/hybrid-search-api.git
cd hybrid-search-api
cp .env.example .env  # LLM_API_KEY (+ ggf. LLM_BASE_URL) eintragen

docker compose up -d  # startet Elasticsearch + API

pip install -e ".[dev]"
python scripts/seed_data.py  # Beispieldaten indexieren - laedt beim allerersten
                              # Lauf einmalig das Embedding-Modell (~80MB)
```

### Datenschutz-Betriebsmodus (Data Sovereignty)

Der LLM-Client funktioniert mit jedem OpenAI-kompatiblen Endpunkt - relevant
fuer ein reales Szenario: Daten, die die eigene Infrastruktur nicht verlassen
duerfen (DSGVO, regulierte Branchen). `docker compose --profile local-llm up`
startet einen lokalen [llama.cpp](https://github.com/ggml-org/llama.cpp)-Server
neben Elasticsearch und der API - der RAG-Schritt macht dann keinen externen
Aufruf mehr. Siehe [ADR-0002](docs/adr/0002-llama-server-for-data-sovereignty-deployments.md)
fuer die Begruendung, warum llama-server statt des bekannteren Ollama
(Kurzfassung: Ollama erzwingt standardmaessig keine API-Key-Pruefung, wodurch
die eigene Fehlerbehandlung fuer Auth-Fehler damit ungetestet bliebe).

```bash
docker compose --profile local-llm up -d   # startet auch den lokalen LLM-Server
```

```bash
# .env
LLM_API_KEY=local-dev-key
LLM_BASE_URL=http://localhost:8090/v1
LLM_MODEL=qwen2.5-1.5b
```

Fuer einfache lokale Entwicklung, bei der Data Sovereignty nicht im Fokus
steht, ist [Ollama](https://ollama.com) einfacher aufzusetzen (siehe der
auskommentierte Block in `.env.example`). Fuer GPU-Produktionsbetrieb
funktioniert derselbe `LLM_BASE_URL`-Tausch auch mit vLLM oder TGI - der App
ist es egal, welcher OpenAI-kompatible Server dahinter steht.

### Test mit einem groesseren, fachfremden Korpus

Die 10 Beispieldokumente in `seed_data.py` handeln bewusst von Such-/RAG-Konzepten
selbst - gut fuer eine saubere Demo, zeigt aber nichts ueber Skalierung.
Dafuer laedt `scripts/seed_nfcorpus.py`
[NFCorpus](https://github.com/beir-cellar/beir) (~3.600 medizinische
Dokumente, ein anerkannter IR-Benchmark) in einen eigenen Index, ohne den
Standard-Index anzuruehren:

```bash
python scripts/seed_nfcorpus.py            # indexiert in '<ELASTICSEARCH_INDEX>_nfcorpus'
ELASTICSEARCH_INDEX=documents_nfcorpus docker compose up -d --build api
```

## Nutzung

`POST /search` mit `{"query": "...", "top_k": 5, "use_llm_answer": true, "lang": "de"}` -
`lang` ist `"en"` (Standard) oder `"de"` und steuert die Sprache der RAG-Antwort
sowie der Fehlermeldungen. Ein echtes Beispiel inkl. Antwort steht oben unter
"Beispiel (echter Output)".

Mit `"agentic": true` entscheidet das LLM selbst, wann/wie es die Suche
aufruft (ueber das projekteigene MCP-Tool `search`, in-process aufgerufen)
statt der festen Suche-dann-Antwort-Pipeline zu folgen - sinnvoll bei
vagen Anfragen, die eine verfeinerte Nachsuche brauchen koennten. Standard
ist `false` (feste Pipeline, wie oben). `use_llm_answer` greift im agentic
Modus nicht - die agentic-Schleife nutzt das LLM immer zum Entscheiden und
Antworten.

Interaktive API-Doku (Swagger): http://localhost:8000/docs

### MCP-Server

Dieselbe Suche steht zusaetzlich als [MCP](https://modelcontextprotocol.io)-Tool
fuer MCP-Clients (Claude Desktop, Claude Code, etc.) zur Verfuegung - als
Ergaenzung neben der REST-API, nicht als Ersatz. In der MCP-Konfiguration des
Clients eintragen:

```json
{
  "mcpServers": {
    "hybrid-search-api": {
      "command": "python",
      "args": ["-m", "hybrid_search_api.mcp_server"],
      "cwd": "/pfad/zu/hybrid-search-api"
    }
  }
}
```

Stellt ein Tool bereit, `search(query, top_k=10, use_llm_answer=True, lang="en")`,
das dieselbe `answer_search()`-Logik wie der REST-Endpunkt nutzt.

## Tests

```bash
pytest -v
ruff check .
```

## Tech-Stack

Python 3.11+ - FastAPI - Elasticsearch - OpenAI-kompatible LLM-Anbindung - MCP - Docker - pytest - ruff - GitHub Actions

## Roadmap

- [x] Echtes Embedding-Modell fuer die Vektorsuche (sentence-transformers, all-MiniLM-L6-v2, lokal)
- [ ] Reranking der Top-Treffer mit einem Cross-Encoder
- [ ] Query-Caching
- [ ] Auth (API-Key) fuer den `/search`-Endpunkt

## Lizenz

MIT - siehe [LICENSE](LICENSE)
