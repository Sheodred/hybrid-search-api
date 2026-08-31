# Architektur

**Sprache:** [English](architecture.md) | **Deutsch**

```
Client
  |
  v
FastAPI (/search)
  |
  +--> Elasticsearch: BM25-Suche (+ Highlight + Facetten-Aggs)
  |                 + kNN-Suche          -> Reciprocal Rank Fusion
  |    beide durch denselben Filter-Kontext eingegrenzt
  |
  +--> LLM (OpenAI-kompatibler Endpunkt): Query-Verstaendnis / RAG-Antwortsynthese
        auf Basis der passenden Textstellen der Top-Treffer
```

## Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/health` | Liveness der API selbst |
| GET | `/health/elasticsearch` | Cluster-Status von Elasticsearch |
| POST | `/search` | Hybrid Search + optionale RAG-Antwort. Nimmt `filters` entgegen; liefert `highlights` pro Treffer sowie `facets` und `word_count_stats` |
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
   Ein `filters`-Objekt im Request wird zu einem gemeinsamen Filter-Kontext
   fuer beide Haelften - auf der Vektorseite als kNN-**Pre-Filter**, damit der
   Kandidatenpool aus der gefilterten Teilmenge gezogen und nicht erst
   nachtraeglich beschnitten wird.
3. Optional (`use_llm_answer=true` **und** mindestens ein Treffer vorhanden)
   werden die Top-Treffer als Kontext an den konfigurierten LLM-Endpunkt
   uebergeben, der daraus eine kurze, quellenbasierte Antwort formuliert
   (RAG-Pattern). Uebergeben werden dabei die *hervorgehobenen Textstellen*
   statt ganzer Dokumente, sofern das Highlighting etwas gefunden hat -
   weniger Tokens, und das Modell bleibt bei der Stelle, die tatsaechlich
   gematcht hat. Das Feld `lang` (`"en"` Standard oder `"de"`) steuert
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

Die Vektoren werden mit explizit gesetzter `int8_hnsw`-Quantisierung
gespeichert: rund ein Viertel der Groesse roher float32-Vektoren bei praktisch
unveraenderter Recall-Qualitaet. Die explizite Angabe fixiert zugleich das
Verhalten - ES 9.x waehlt bei 384 Dimensionen sonst `bbq_hnsw`.

## Anpassbare Suchkonfiguration

Zwei Stellen sind bewusst getrennt und unabhaengig voneinander editierbar:

- **`search/index_config.py`** - Analyzer, Filter (Stemming, Stoppwoerter) und
  Feld-Mappings. Hier stellt man z. B. auf eine andere Sprache um, passt die
  Embedding-Dimension an oder ergaenzt Synonyme.
- **`search/queries.py`** - die eigentliche Such-Query-DSL (Feld-Boosts,
  Fuzziness, Phrasen-Slop, Filter-Klauseln, Highlight-Konfiguration,
  Facetten-Aggregationen, Groesse des kNN-Kandidatenpools). Hier wird getunt,
  *wie* gesucht wird, unabhaengig von der Fusion-Logik in `hybrid_search.py`.

Diese Trennung spiegelt die Trennung bei den Prompts wider (`ai/prompts.py`):
Konfiguration/Template an einem Ort, Verwendung/Orchestrierung an einem
anderen.

Beide Builder werden nach [`docs/search/`](search/) als JSON gerendert - eine
Datei pro Konzept, jeweils mit kurzer Erklaerung, was sie zeigt, welches
Mapping-Feld sie moeglich macht und was man zum Ausprobieren aendern kann.
`tests/test_config_snapshots.py` haelt die Dateien synchron - editiert wird
das Python, nicht das JSON. `python scripts/run_examples.py` fuehrt alle
Beispiele gegen einen lokalen Cluster aus.

### Was wo demonstriert wird

| Konzept | Wo |
|---|---|
| Getrennte Index-/Such-Analyzer, `synonym_graph` | `index_config.py` -> `index_settings.json` |
| `.exact`-/`.keyword`-Multi-Fields, `normalizer` | `index_config.py` -> `index_settings.json` |
| `copy_to`-Sammelfeld, `index: false`, `dynamic: strict` | `index_config.py` -> `index_settings.json` |
| `dense_vector` + `int8_hnsw` + HNSW-Parameter | `index_config.py` -> `index_settings.json` |
| `bool` must/should/filter, `most_fields`, `match_phrase` + `slop` | `queries.py` -> `example_query_text.json` |
| Gemeinsamer Filter-Kontext | `queries.py` -> `example_query_bm25_filtered.json` |
| kNN-Pre-Filter | `queries.py` -> `example_query_knn_prefiltered.json` |
| `unified`-Highlighter (+ passagenbasiertes RAG) | `queries.py` -> `example_highlight.json` |
| `terms`-/`date_histogram`-/`stats`-Aggregationen | `queries.py` -> `example_aggs_facets.json` |
| `function_score`-`gauss`-Decay (nur Referenz) | `queries.py` -> `example_function_score_recency.json` |
| Reciprocal Rank Fusion, `source_excludes` | `hybrid_search.py` |

## Warum Reciprocal Rank Fusion?

RRF kombiniert zwei Ranglisten, ohne dass man BM25- und Vektor-Scores (die auf
komplett unterschiedlichen Skalen liegen) von Hand gegeneinander gewichten
muss. Das macht es zu einem robusten Standardverfahren fuer Hybrid Search.

Die Fusion laeuft in `search/hybrid_search.py` und nicht ueber den nativen
`rrf`-Retriever von Elasticsearch, weil dieser lizenzpflichtig ist und auf
einer `basic`-Lizenz mit 403 antwortet - siehe
[ADR-0003](adr/0003-elasticsearch-9-upgrade.md).
