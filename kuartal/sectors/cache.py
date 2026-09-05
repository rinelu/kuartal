"""
Short-TTL in-memory cache for Sectors API responses.

Process-local and not persistent. It only avoids repeated requests for the
same endpoint and params during a pipeline run, such as multiple tickers
requesting the same sector data.
"""

from __future__ import annotations
from typing import Any

import time

class TTLCache:
    def __init__(self, ttl_seconds: float = 60.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    @staticmethod
    def make_key(url: str, params: dict[str, Any] | None) -> str:
        if not params: return url

        sorted_params = sorted(params.items(), key=lambda kv: kv[0])
        query = "&".join(f"{k}={v}" for k, v in sorted_params)
        return f"{url}?{query}"

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None: return None

        stored_at, value = entry
        if time.monotonic() - stored_at > self.ttl_seconds:
            self._store.pop(key, None)
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.monotonic(), value)

    def clear(self) -> None:
        self._store.clear()
