# Architektur

**Sprache:** [English](architecture.md) | **Deutsch**

```
Client
  |
  v
FastAPI (/search)
  |
  +--> Elasticsearch: BM25-Suche + kNN-Suche -> Reciprocal Rank Fusion
  |
  +--> LLM (OpenAI-kompatibler Endpunkt): Query-Verstaendnis / RAG-Antwortsynthese
        auf Basis der Top-Suchergebnisse
```

## Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/health` | Liveness der API selbst |
| GET | `/health/elasticsearch` | Cluster-Status von Elasticsearch |
| POST | `/search` | Hybrid Search + optionale RAG-Antwort |
| GET | `/index` | Mapping und Dokumentanzahl des Index |
| GET | `/index/documents` | Indexierte Dokumente durchblaettern (paginiert, `limit`/`offset`) |

Bewusst ohne Authentifizierung (siehe Roadmap in der README) - fuer eine
Demo-/Portfolio-Instanz ausreichend, fuer echten Produktivbetrieb waeren
zumindest `/index*` schuetzenswert. Ist Elasticsearch selbst nicht
erreichbar, liefert jeder Endpunkt (nicht nur die Index-Routen) einen
klaren 502 statt eines nackten 500ers - siehe den globalen Exception-Handler
in `main.py`.

## Ablauf einer Anfrage

1. Client schickt eine natuerlichsprachliche Anfrage an `POST /search`.
2. Der Search-Layer fuehrt immer BM25-Suche aus; kNN-Suche kommt nur hinzu,
   wenn eine Query-Embedding vorliegt (siehe Abschnitt "Embeddings" fuer den
   Fallback). Liegen beide Ergebnislisten vor, werden sie per Reciprocal Rank
   Fusion (RRF) fusioniert - sonst zaehlt allein das BM25-Ranking.
3. Optional (`use_llm_answer=true` **und** mindestens ein Treffer vorhanden)
   werden die Top-Treffer als Kontext an den konfigurierten LLM-Endpunkt
   uebergeben, der daraus eine kurze, quellenbasierte Antwort formuliert
   (RAG-Pattern). Das Feld `lang` (`"en"` Standard oder `"de"`) steuert
   sowohl die Sprache dieser Antwort als auch die Sprache der folgenden
   Fehlermeldungen. Fehler beim LLM-Call (falscher Key, unbekanntes Modell,
   Endpunkt nicht erreichbar, ...) werden als aussagekraeftige 502-Antworten
   durchgereicht statt als nackter 500er - siehe `api/routes.py`.
4. Die Antwort inkl. der zugrunde liegenden Treffer geht an den Client zurueck.

## Embeddings

Query und Dokumente werden mit einem lokalen `sentence-transformers`-Modell
(`all-MiniLM-L6-v2`, 384 Dimensionen) eingebettet - kein externer API-Call,
keine Zusatzkosten pro Suche. Schlaegt das Laden des Modells fehl, faellt
`/search` automatisch auf reines BM25 zurueck (siehe `api/routes.py`).

## Anpassbare Suchkonfiguration

Zwei Stellen sind bewusst getrennt und unabhaengig voneinander editierbar:

- **`search/index_config.py`** - Analyzer, Filter (Stemming, Stoppwoerter) und
  Feld-Mappings. Hier stellt man z. B. auf eine andere Sprache um, passt die
  Embedding-Dimension an oder ergaenzt Synonyme.
- **`search/queries.py`** - die eigentliche Such-Query-DSL (Feld-Boosts,
  Fuzziness, Groesse des kNN-Kandidatenpools). Hier wird getunt, *wie*
  gesucht wird, unabhaengig von der Fusion-Logik in `hybrid_search.py`.

Diese Trennung spiegelt die Trennung bei den Prompts wider (`ai/prompts.py`):
Konfiguration/Template an einem Ort, Verwendung/Orchestrierung an einem
anderen.

## Warum Reciprocal Rank Fusion?

RRF kombiniert zwei Ranglisten, ohne dass man BM25- und Vektor-Scores (die auf
komplett unterschiedlichen Skalen liegen) von Hand gegeneinander gewichten
muss. Das macht es zu einem robusten Standardverfahren fuer Hybrid Search.
