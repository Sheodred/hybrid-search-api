from hybrid_search_api.ai.prompts import build_agentic_system_prompt, build_rag_prompt


def test_system_prompt_instructs_plain_text_answer_en():
    system, _ = build_rag_prompt("q", [{"title": "T", "content": "C"}], lang="en")

    assert "markdown" in system.lower()


def test_system_prompt_instructs_plain_text_answer_de():
    system, _ = build_rag_prompt("q", [{"title": "T", "content": "C"}], lang="de")

    assert "markdown" in system.lower()


def test_agentic_system_prompt_instructs_no_nested_llm_answer_en():
    prompt = build_agentic_system_prompt(lang="en")

    assert "use_llm_answer" in prompt
    assert "false" in prompt.lower()


def test_agentic_system_prompt_instructs_no_nested_llm_answer_de():
    prompt = build_agentic_system_prompt(lang="de")

    assert "use_llm_answer" in prompt
