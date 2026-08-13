"""Prompt templates for the RAG layer. Keeping them versioned in one place makes
it easy to track how a wording change affects answer quality over time.
"""

RAG_ANSWER_SYSTEM_V1_EN = """\
Answer the user's question using only the provided search results.
If the results don't answer the question, say so explicitly - don't make anything up.
Answer concisely and state what your answer is based on (e.g. document title).
Respond in plain prose - no markdown formatting (no headings, bold, or tables).
"""

RAG_ANSWER_SYSTEM_V1_DE = """\
Du beantwortest Nutzerfragen ausschliesslich auf Basis der bereitgestellten Suchergebnisse.
Wenn die Ergebnisse die Frage nicht beantworten, sag das explizit - erfinde nichts dazu.
Antworte knapp und nenne, worauf sich deine Antwort stuetzt (z. B. Dokumenttitel).
Antworte in reinem Fliesstext - kein Markdown (keine Ueberschriften, Fettungen oder Tabellen).
"""

_SYSTEM_PROMPTS = {
    "v1": {"en": RAG_ANSWER_SYSTEM_V1_EN, "de": RAG_ANSWER_SYSTEM_V1_DE},
}

_NO_TITLE = {"en": "Untitled", "de": "Ohne Titel"}
_USER_PROMPT_TEMPLATE = {
    "en": "Question: {query}\n\nSearch results:\n{context}",
    "de": "Frage: {query}\n\nSuchergebnisse:\n{context}",
}


def build_rag_prompt(
    query: str, hits: list[dict], version: str = "v1", lang: str = "en"
) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for the given prompt version and language."""
    context = "\n\n".join(
        f"[{i + 1}] {hit.get('title', _NO_TITLE[lang])}: {hit.get('content', '')[:500]}"
        for i, hit in enumerate(hits)
    )
    user_prompt = _USER_PROMPT_TEMPLATE[lang].format(query=query, context=context)
    if version not in _SYSTEM_PROMPTS:
        raise ValueError(f"Unknown prompt version: {version}")
    return _SYSTEM_PROMPTS[version][lang], user_prompt
