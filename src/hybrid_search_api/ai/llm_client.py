"""Thin wrapper around an OpenAI-compatible chat completions endpoint.

Works against OpenAI directly, or - just as well - a gateway/proxy that speaks
the same API, like an internal company LLM hub sitting in front of Anthropic,
Azure OpenAI, or a self-hosted model. The provider is just a base_url + model
string away; the rest of the app never talks to the SDK directly.
"""

import logging

from openai import APIError, APIStatusError, OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from hybrid_search_api.config import Settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: Settings):
        self._client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
        self._model = settings.llm_model

    @retry(
        retry=retry_if_exception_type((APIError, APIStatusError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        """Single non-streaming completion, with automatic retry on transient API errors."""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except (APIError, APIStatusError):
            logger.exception("LLM API call failed")
            raise

    def stream(self, system: str, prompt: str, max_tokens: int = 1024):
        """Yields text chunks as they arrive - use for a responsive, incremental UI."""
        chat_stream = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        for chunk in chat_stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
