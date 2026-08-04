# Architektur

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

## Ablauf einer Anfrage

1. Client schickt eine natuerlichsprachliche Anfrage an `POST /search`.
2. Der Search-Layer fuehrt immer BM25-Suche aus; kNN-Suche kommt nur hinzu,
   wenn eine Query-Embedding vorliegt (siehe Abschnitt "Embeddings" fuer den
   Fallback). Liegen beide Ergebnislisten vor, werden sie per Reciprocal Rank
   Fusion (RRF) fusioniert - sonst zaehlt allein das BM25-Ranking.
3. Optional (`use_llm_answer=true` **und** mindestens ein Treffer vorhanden)
   werden die Top-Treffer als Kontext an den konfigurierten LLM-Endpunkt
   uebergeben, der daraus eine kurze, quellenbasierte Antwort formuliert
   (RAG-Pattern). Fehler beim LLM-Call (falscher Key, unbekanntes Modell,
   Endpunkt nicht erreichbar, ...) werden als aussagekraeftige 502-Antworten
   durchgereicht statt als nackter 500er - siehe `api/routes.py`.
4. Die Antwort inkl. der zugrunde liegenden Treffer geht an den Client zurueck.

## Embeddings

Query und Dokumente werden mit einem lokalen `sentence-transformers`-Modell
(`all-MiniLM-L6-v2`, 384 Dimensionen) eingebettet - kein externer API-Call,
keine Zusatzkosten pro Suche. Schlaegt das Laden des Modells fehl, faellt
`/search` automatisch auf reines BM25 zurueck (siehe `api/routes.py`).

## Warum Reciprocal Rank Fusion?

RRF kombiniert zwei Ranglisten, ohne dass man BM25- und Vektor-Scores (die auf
komplett unterschiedlichen Skalen liegen) von Hand gegeneinander gewichten
muss. Das macht es zu einem robusten Standardverfahren fuer Hybrid Search.
