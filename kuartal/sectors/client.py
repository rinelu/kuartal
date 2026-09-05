"""
Lightweight GET client for the Sectors API.

Responsible for authentication headers and request retries. Endpoint-specific
logic is handled separately in `endpoints.py`.
"""

from __future__ import annotations
from typing import Any
from kuartal.config import settings
from kuartal.sectors.cache import TTLCache

import time
import httpx

class SectorsAPIError(RuntimeError):
    """Raised when the Sectors API returns a non-2xx response after all retries."""

class SectorsRateLimitError(SectorsAPIError):
    """Raised when the Sectors API returns 429 after all retries are exhausted."""

class SectorsClient:
    def __init__(
        self,
        api_key:     str | None  = None,
        base_url:    str | None  = None,
        max_retries: int         = 3,
        timeout:     float       = 10.0,
        cache_ttl_seconds: float = 60.0
    ) -> None:
        self.api_key     = api_key or settings.sectors_api_key
        self.base_url    = (base_url or settings.sectors_base_url).rstrip("/")
        self.max_retries = max_retries
        self._client     = httpx.Client(timeout=timeout)
        self._cache      = TTLCache(ttl_seconds=cache_ttl_seconds)

    def get(self, path: str, params: dict[str, Any] | None = None, use_cache: bool = True) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        cache_key = self._cache.make_key(url, params)

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None: return cached

        headers = { "Authorization": self.api_key }
        last_exc: Exception | None = None
        last_status: int | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self._client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                if use_cache: self._cache.set(cache_key, data)

                return data

            except httpx.HTTPStatusError as exc:
                last_exc = exc
                last_status = exc.response.status_code
                if exc.response.status_code == 429:
                    time.sleep(2**attempt)
                    continue

                if exc.response.status_code < 500: break

                time.sleep(2**attempt)

            except httpx.RequestError as exc:
                last_exc = exc
                time.sleep(2**attempt)

        if last_status == 429:
            raise SectorsRateLimitError(f"GET {url} rate-limited after {self.max_retries} attempts") from last_exc

        raise SectorsAPIError(f"GET {url} failed after {self.max_retries} attempts") from last_exc

    def close(self) -> None:
        self._client.close()
