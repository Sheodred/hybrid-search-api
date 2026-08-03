"""Thin wrapper around the Anthropic API: centralizes error handling, retries,
and streaming so the rest of the app never talks to the SDK directly.
"""

import logging

from anthropic import Anthropic, APIError, APIStatusError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from hybrid_search_api.config import Settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: Settings):
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    @retry(
        retry=retry_if_exception_type((APIError, APIStatusError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        """Single non-streaming completion, with automatic retry on transient API errors."""
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(block.text for block in response.content if block.type == "text")
        except (APIError, APIStatusError):
            logger.exception("Anthropic API call failed")
            raise

    def stream(self, system: str, prompt: str, max_tokens: int = 1024):
        """Yields text chunks as they arrive - use for a responsive, incremental UI."""
        with self._client.messages.stream(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            yield from stream.text_stream
