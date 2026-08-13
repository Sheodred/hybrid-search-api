from hybrid_search_api.ai.prompts import build_rag_prompt


def test_system_prompt_instructs_plain_text_answer_en():
    system, _ = build_rag_prompt("q", [{"title": "T", "content": "C"}], lang="en")

    assert "markdown" in system.lower()


def test_system_prompt_instructs_plain_text_answer_de():
    system, _ = build_rag_prompt("q", [{"title": "T", "content": "C"}], lang="de")

    assert "markdown" in system.lower()
