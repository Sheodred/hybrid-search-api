from unittest.mock import MagicMock, patch

from hybrid_search_api.ai.llm_client import LLMClient
from hybrid_search_api.config import Settings


@patch("hybrid_search_api.ai.llm_client.OpenAI")
def test_complete_returns_text_from_response(mock_openai_cls):
    mock_message = MagicMock(content="Test answer")
    mock_choice = MagicMock(message=mock_message)
    mock_response = MagicMock(choices=[mock_choice])
    mock_openai_cls.return_value.chat.completions.create.return_value = mock_response

    client = LLMClient(Settings())
    result = client.complete(system="sys", prompt="question")

    assert result == "Test answer"
