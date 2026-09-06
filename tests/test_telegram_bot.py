"""
Tests for `TelegramBot`'s HTTP/retry logic and per-user chat id routing.
"""

from __future__ import annotations

import httpx
import respx

from kuartal.delivery.telegram_bot import TelegramBot

SEND_URL = "https://api.telegram.org/bottest-token/sendMessage"


def _bot(**kwargs) -> TelegramBot:
    return TelegramBot(bot_token="test-token", **kwargs)


@respx.mock
def test_send_message_happy_path():
    respx.post(SEND_URL).mock(return_value=httpx.Response(200, json={"ok": True}))

    result = _bot().send_message("12345", "hello")

    assert result.status == "sent"
    assert result.chat_id == "12345"
    assert result.sent_at is not None


@respx.mock
def test_send_message_retries_then_succeeds_on_5xx(monkeypatch):
    monkeypatch.setattr("kuartal.delivery.telegram_bot.time.sleep", lambda _: None)
    route = respx.post(SEND_URL).mock(side_effect=[
        httpx.Response(500),
        httpx.Response(200, json={"ok": True}),
    ])

    result = _bot(max_retries=3).send_message("12345", "hello")

    assert result.status == "sent"
    assert route.call_count == 2


@respx.mock
def test_send_message_does_not_retry_4xx(monkeypatch):
    monkeypatch.setattr("kuartal.delivery.telegram_bot.time.sleep", lambda _: None)
    route = respx.post(SEND_URL).mock(return_value=httpx.Response(400, json={"ok": False}))

    result = _bot(max_retries=3).send_message("bad-chat-id", "hello")

    assert result.status == "failed"
    assert route.call_count == 1  # 4xx is not worth retrying


@respx.mock
def test_send_message_fails_after_exhausting_retries_on_5xx(monkeypatch):
    monkeypatch.setattr("kuartal.delivery.telegram_bot.time.sleep", lambda _: None)
    respx.post(SEND_URL).mock(return_value=httpx.Response(503))

    result = _bot(max_retries=2).send_message("12345", "hello")

    assert result.status == "failed"
    assert result.error is not None


class _FakeDb:
    """Minimal stand-in for storage/db.py's Database, just what
    send_to_watchers needs."""

    def __init__(self, users_for_ticker, chat_ids=None):
        self._users_for_ticker = users_for_ticker
        self._chat_ids = chat_ids or {}

    def list_users_for_ticker(self, ticker):
        return self._users_for_ticker

    def get_chat_id(self, user):
        return self._chat_ids.get(user)


@respx.mock
def test_send_to_watchers_uses_explicit_chat_ids_dict():
    respx.post(SEND_URL).mock(return_value=httpx.Response(200, json={"ok": True}))
    db = _FakeDb(users_for_ticker=["alice"])

    results = _bot().send_to_watchers(db, "BBRI", "verdict text", chat_ids={"alice": "111"})

    assert len(results) == 1
    assert results[0].chat_id == "111"
    assert results[0].status == "sent"


@respx.mock
def test_send_to_watchers_falls_back_to_persisted_chat_id():
    respx.post(SEND_URL).mock(return_value=httpx.Response(200, json={"ok": True}))
    db = _FakeDb(users_for_ticker=["bob"], chat_ids={"bob": "222"})

    results = _bot().send_to_watchers(db, "BBRI", "verdict text")

    assert results[0].chat_id == "222"
    assert results[0].status == "sent"


def test_send_to_watchers_skips_users_with_no_chat_id_configured():
    db = _FakeDb(users_for_ticker=["carol"])

    results = _bot().send_to_watchers(db, "BBRI", "verdict text")

    assert results[0].status == "failed"
    assert "no chat id" in results[0].error
