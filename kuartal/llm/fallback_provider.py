"""
Fallback LLM provider, used when the primary provider (Gemini) errors or
rate-limits.
"""

from __future__ import annotations

import time
import httpx

from kuartal.config import settings
from kuartal.llm.base import LLMProvider, LLMProviderError, LLMRateLimitError
from kuartal.llm.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from kuartal.pipeline.verdict import VerdictPayload

_BASE_URLS = {
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
}

class FallbackProviderUnavailable(LLMProviderError):
    """Raised when `settings.llm_fallback_provider` is "none" or unrecognized."""

class OpenAICompatibleProvider(LLMProvider):
    """Chat-completions provider for any OpenAI-compatible API (OpenRouter, Groq)."""

    def __init__(
        self,
        provider_name: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        timeout: float = 20.0,
    ) -> None:
        self.provider_name = provider_name or settings.llm_fallback_provider
        if self.provider_name not in _BASE_URLS:
            raise FallbackProviderUnavailable(f"No fallback provider configured (llm_fallback_provider={self.provider_name!r})")

        self.base_url    = _BASE_URLS[self.provider_name]
        self.api_key     = api_key or settings.llm_fallback_api_key
        self.model       = model or settings.llm_fallback_model
        self.max_retries = max_retries
        self._client     = httpx.Client(timeout=timeout)

    def generate_verdict(self, payload: VerdictPayload) -> str:
        headers = { "Authorization": f"Bearer {self.api_key}" }
        body = {
            "model": self.model,
            "messages": [
                { "role": "system", "content": SYSTEM_PROMPT },
                { "role": "user", "content": build_user_prompt(payload) },
            ],
            "temperature": 0.2,
            "max_tokens": 200,
        }

        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self._client.post(self.base_url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()

            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code == 429:
                    time.sleep(2**attempt)
                    continue

                if exc.response.status_code < 500:
                    raise LLMProviderError(f"{self.provider_name} request failed: {exc}") from exc

                time.sleep(2**attempt)

            except httpx.RequestError as exc:
                last_exc = exc
                time.sleep(2**attempt)

            except (KeyError, IndexError) as exc:
                raise LLMProviderError(f"Unexpected {self.provider_name} response shape") from exc

        raise LLMRateLimitError(f"{self.provider_name} rate-limited or unreachable after {self.max_retries} attempts") from last_exc

    def close(self) -> None:
        self._client.close()
