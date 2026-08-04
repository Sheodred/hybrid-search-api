"""Utility script: indexes a small set of sample documents into Elasticsearch,
including their embeddings, so the API has something to search against
(BM25 and kNN) right after setup.

Usage:
    python scripts/seed_data.py
"""

from hybrid_search_api.config import get_settings
from hybrid_search_api.search.elasticsearch_client import build_client, ensure_index
from hybrid_search_api.search.embeddings import embed_many

SAMPLE_DOCS = [
    {
        "title": "Elasticsearch Grundlagen",
        "content": (
            "Elasticsearch ist eine verteilte Such- und Analyse-Engine auf Basis von "
            "Apache Lucene. Sie eignet sich fuer Volltextsuche, strukturierte Suche und "
            "Analytics nahezu in Echtzeit. Daten werden in Indizes organisiert, die "
            "intern auf mehrere Shards verteilt werden."
        ),
    },
    {
        "title": "Vektorsuche und Embeddings",
        "content": (
            "Bei der Vektorsuche werden Texte als hochdimensionale Zahlenvektoren "
            "(Embeddings) repraesentiert. Aehnliche Inhalte liegen im Vektorraum nah "
            "beieinander, wodurch semantisch verwandte Dokumente gefunden werden, auch "
            "wenn keine woertliche Uebereinstimmung vorliegt."
        ),
    },
    {
        "title": "Retrieval-Augmented Generation (RAG)",
        "content": (
            "RAG kombiniert eine Suchkomponente mit einem Sprachmodell: Zunaechst "
            "werden relevante Dokumente abgerufen, anschliessend generiert das Modell "
            "eine Antwort auf Basis dieser Quellen. Das reduziert Halluzinationen und "
            "macht Antworten nachvollziehbar."
        ),
    },
    {
        "title": "BM25-Ranking",
        "content": (
            "BM25 ist eine Ranking-Funktion fuer die klassische Volltextsuche, die "
            "Termfrequenz, inverse Dokumentfrequenz und Dokumentlaenge beruecksichtigt. "
            "Sie ist der Standard-Scoring-Algorithmus in Elasticsearch und liefert bei "
            "exakten Begriffstreffern sehr gute Ergebnisse."
        ),
    },
    {
        "title": "Reciprocal Rank Fusion (RRF)",
        "content": (
            "RRF fusioniert mehrere Ranglisten unterschiedlicher Suchverfahren, ohne "
            "dass deren Scores auf eine gemeinsame Skala gebracht werden muessen. Jedes "
            "Dokument erhaelt Punkte basierend auf seinem Rang in jeder Liste, was RRF "
            "robust gegenueber Ausreissern macht."
        ),
    },
    {
        "title": "Approximate Nearest Neighbor Search (HNSW)",
        "content": (
            "Elasticsearch nutzt fuer die kNN-Suche den HNSW-Algorithmus (Hierarchical "
            "Navigable Small World), um aehnliche Vektoren approximativ, aber sehr "
            "schnell zu finden. Der Parameter num_candidates steuert dabei die Balance "
            "zwischen Suchgeschwindigkeit und Genauigkeit."
        ),
    },
    {
        "title": "Sentence-Transformer-Modelle",
        "content": (
            "Sentence-Transformer-Modelle wie all-MiniLM-L6-v2 wandeln ganze Saetze in "
            "Embedding-Vektoren um, statt einzelne Woerter isoliert zu betrachten. "
            "Dadurch erfassen sie Kontext und Bedeutung besser als klassische "
            "Wort-Embeddings."
        ),
    },
    {
        "title": "Volltextsuche vs. semantische Suche",
        "content": (
            "Volltextsuche findet Dokumente ueber exakte oder fuzzy "
            "Wortuebereinstimmungen, waehrend semantische Suche auf "
            "Bedeutungsaehnlichkeit basiert. Hybrid Search kombiniert beide Ansaetze, "
            "um sowohl praezise Begriffstreffer als auch inhaltlich verwandte "
            "Ergebnisse zu liefern."
        ),
    },
    {
        "title": "Analyzer und Tokenisierung",
        "content": (
            "Ein Elasticsearch-Analyzer zerlegt Text in Tokens und normalisiert sie, "
            "etwa durch Kleinschreibung, Stemming oder Stoppwort-Entfernung. "
            "Sprachspezifische Analyzer wie der German-Analyzer verbessern die "
            "Trefferquote bei deutschsprachigen Inhalten deutlich."
        ),
    },
    {
        "title": "Prompt Engineering fuer RAG-Systeme",
        "content": (
            "Die Formulierung des System-Prompts entscheidet massgeblich darueber, ob "
            "ein RAG-System nur auf Basis der gelieferten Quellen antwortet oder zu "
            "Halluzinationen neigt. Klare Anweisungen, explizite Quellenverweise und "
            "Versionierung der Prompts erhoehen die Nachvollziehbarkeit."
        ),
    },
]


def main() -> None:
    settings = get_settings()
    client = build_client(settings)
    ensure_index(client, settings.elasticsearch_index)

    print("Computing embeddings (first run downloads the model, ~80MB)...")
    vectors = embed_many([doc["content"] for doc in SAMPLE_DOCS])

    for i, (doc, vector) in enumerate(zip(SAMPLE_DOCS, vectors, strict=True), start=1):
        client.index(
            index=settings.elasticsearch_index,
            id=str(i),
            document={**doc, "embedding": vector},
        )
    client.indices.refresh(index=settings.elasticsearch_index)
    print(
        f"Indexed {len(SAMPLE_DOCS)} sample documents (with embeddings) "
        f"into '{settings.elasticsearch_index}'."
    )


if __name__ == "__main__":
    main()
