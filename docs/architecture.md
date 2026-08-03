# Architektur

```
Client
  |
  v
FastAPI (/search)
  |
  +--> Elasticsearch: BM25-Suche + kNN-Suche -> Reciprocal Rank Fusion
  |
  +--> Anthropic API: Query-Verstaendnis / RAG-Antwortsynthese
        auf Basis der Top-Suchergebnisse
```

## Ablauf einer Anfrage

1. Client schickt eine natuerlichsprachliche Anfrage an `POST /search`.
2. Der Search-Layer fuehrt BM25- und kNN-Suche gegen Elasticsearch aus und
   fusioniert die Ergebnislisten per Reciprocal Rank Fusion (RRF).
3. Optional (`use_llm_answer=true`) werden die Top-Treffer als Kontext an die
   Anthropic API uebergeben, die daraus eine kurze, quellenbasierte Antwort
   formuliert (RAG-Pattern).
4. Die Antwort inkl. der zugrunde liegenden Treffer geht an den Client zurueck.

## Warum Reciprocal Rank Fusion?

RRF kombiniert zwei Ranglisten, ohne dass man BM25- und Vektor-Scores (die auf
komplett unterschiedlichen Skalen liegen) von Hand gegeneinander gewichten
muss. Das macht es zu einem robusten Standardverfahren fuer Hybrid Search.
