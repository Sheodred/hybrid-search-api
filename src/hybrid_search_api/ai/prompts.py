"""Prompt templates for the RAG layer. Keeping them versioned in one place makes
it easy to track how a wording change affects answer quality over time.
"""

RAG_ANSWER_SYSTEM_V1 = """\
Du beantwortest Nutzerfragen ausschliesslich auf Basis der bereitgestellten Suchergebnisse.
Wenn die Ergebnisse die Frage nicht beantworten, sag das explizit - erfinde nichts dazu.
Antworte knapp und nenne, worauf sich deine Antwort stuetzt (z. B. Dokumenttitel).
"""


def build_rag_prompt(query: str, hits: list[dict], version: str = "v1") -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for the given prompt version."""
    context = "\n\n".join(
        f"[{i + 1}] {hit.get('title', 'Ohne Titel')}: {hit.get('content', '')[:500]}"
        for i, hit in enumerate(hits)
    )
    user_prompt = f"Frage: {query}\n\nSuchergebnisse:\n{context}"
    if version == "v1":
        return RAG_ANSWER_SYSTEM_V1, user_prompt
    raise ValueError(f"Unknown prompt version: {version}")
