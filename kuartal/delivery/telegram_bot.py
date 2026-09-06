"""
Telegram delivery channel for generated verdicts.

For v1, this is the only delivery channel. It sends verdicts to everyone
watching a ticker, tracks delivery status, and retries failed sends so
messages aren't silently lost.

Each watcher gets the verdict sent to their own chat ID instead of using
one hardcoded chat.
"""

from __future__ import annotations

import logging
import time
import httpx
from dataclasses import dataclass
from datetime import datetime, timezone

from kuartal.config import settings

logger = logging.getLogger("kuartal.delivery.telegram")

TELEGRAM_API_BASE = "https://api.telegram.org"

@dataclass
class DeliveryResult:
    channel: str
    chat_id: str
    status: str # "sent" | "failed"
    sent_at: str | None
    error: str | None = None

class TelegramDeliveryError(RuntimeError):
    """Raised when a message could not be delivered after all retries."""

class TelegramBot:
    def __init__(
        self,
        bot_token: str | None = None,
        max_retries: int = 3,
        timeout: float = 10.0,
    ) -> None:
        self.bot_token   = bot_token or settings.telegram_bot_token
        self.max_retries = max_retries
        self._client     = httpx.Client(timeout=timeout)

    def send_message(self, chat_id: str, text: str) -> DeliveryResult:
        """Send `text` to `chat_id`, retrying on failure."""

        url = f"{TELEGRAM_API_BASE}/bot{self.bot_token}/sendMessage"
        last_error: str | None = None

        for attempt in range(self.max_retries):
            try:
                resp = self._client.post(url, json={"chat_id": chat_id, "text": text})
                resp.raise_for_status()
                return DeliveryResult(
                    channel="Telegram",
                    chat_id=chat_id,
                    status="sent",
                    sent_at=datetime.now(timezone.utc).isoformat(),
                )

            except httpx.HTTPStatusError as exc:
                last_error = f"HTTP {exc.response.status_code}"
                if exc.response.status_code < 500: break

                time.sleep(2**attempt)

            except httpx.RequestError as exc:
                last_error = str(exc)
                time.sleep(2**attempt)

        logger.error("Telegram delivery failed chat_id=%s error=%s", chat_id, last_error)
        return DeliveryResult(
            channel="Telegram",
            chat_id=chat_id,
            status="failed",
            sent_at=None,
            error=last_error,
        )

    def send_to_watchers(
        self, db, ticker: str, text: str, chat_ids: dict[str, str] | None = None
    ) -> list[DeliveryResult]:
        """Send `text` to every user watching `ticker`.

        `chat_ids` optionally maps user -> Telegram chat id, overriding the
        persisted `db.get_chat_id(user)` lookup for this call only.
        """

        chat_ids = chat_ids or {}
        results: list[DeliveryResult] = []
        for user in db.list_users_for_ticker(ticker):
            chat_id = chat_ids.get(user) or db.get_chat_id(user) or settings.telegram_chat_id
            if not chat_id:
                logger.warning("No chat id configured for user=%s, skipping delivery", user)
                results.append(DeliveryResult(channel="Telegram", chat_id="", status="failed", sent_at=None, error="no chat id configured"))
                continue

            results.append(self.send_message(chat_id, text))

        return results

    def close(self) -> None:
        self._client.close()
