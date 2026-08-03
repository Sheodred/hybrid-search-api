from unittest.mock import MagicMock, patch

from hybrid_search_api.ai.llm_client import LLMClient
from hybrid_search_api.config import Settings


@patch("hybrid_search_api.ai.llm_client.Anthropic")
def test_complete_returns_text_from_response(mock_anthropic_cls):
    mock_block = MagicMock(type="text", text="Test-Antwort")
    mock_response = MagicMock(content=[mock_block])
    mock_anthropic_cls.return_value.messages.create.return_value = mock_response

    client = LLMClient(Settings())
    result = client.complete(system="sys", prompt="frage")

    assert result == "Test-Antwort"
