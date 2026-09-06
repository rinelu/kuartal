"""
Gemini provider

Uses the Gemini REST API directly with `httpx` instead of the full Google SDK.
Retries rate-limit errors with backoff and maps provider failures to the
shared LLM exceptions so `llm/service.py` can handle failover consistently.
"""

from __future__ import annotations

import time
import httpx

from kuartal.config import settings
from kuartal.llm.base import LLMProvider, LLMProviderError, LLMRateLimitError
from kuartal.llm.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from kuartal.pipeline.verdict import VerdictPayload

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        timeout: float = 20.0,
    ) -> None:
        self.api_key     = api_key or settings.llm_api_key
        self.model       = model or settings.llm_model
        self.max_retries = max_retries
        self._client     = httpx.Client(timeout=timeout)

    def generate_verdict(self, payload: VerdictPayload) -> str:
        url = f"{GEMINI_BASE_URL}/{self.model}:generateContent"
        body = {
            "system_instruction": { "parts": [{ "text": SYSTEM_PROMPT }] },
            "contents": [{ "role": "user", "parts": [{ "text": build_user_prompt(payload) }] }],
            "generationConfig": { "temperature": 0.2, "maxOutputTokens": 200 }
        }

        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self._client.post(url, params={"key": self.api_key}, json=body)
                resp.raise_for_status()
                data = resp.json()
                return self._extract_text(data)

            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code == 429:
                    time.sleep(2**attempt)
                    continue

                if exc.response.status_code < 500:
                    raise LLMProviderError(f"Gemini request failed: {exc}") from exc

                time.sleep(2**attempt)

            except httpx.RequestError as exc:
                last_exc = exc
                time.sleep(2**attempt)

        raise LLMRateLimitError(f"Gemini rate-limited or unreachable after {self.max_retries} attempts") from last_exc

    @staticmethod
    def _extract_text(data: dict) -> str:
        try:
            candidates = data["candidates"]
            parts = candidates[0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts).strip()

        except (KeyError, IndexError) as exc:
            raise LLMProviderError(f"Unexpected Gemini response shape: {data}") from exc

    def close(self) -> None:
        self._client.close()
