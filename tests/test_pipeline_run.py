from __future__ import annotations

import httpx
import pytest
import respx
from typing import cast

from kuartal.llm.base import LLMProvider
from kuartal.pipeline.run import run_for_ticker
from kuartal.sectors.client import SectorsClient
from kuartal.storage.db import Database

BASE_URL = "https://api.sectors.app"


@pytest.fixture(autouse=True)
def _pipeline_stages_enabled(monkeypatch):
    monkeypatch.setattr("kuartal.config.settings.pipeline_enable_llm", True)
    monkeypatch.setattr("kuartal.config.settings.pipeline_enable_delivery", True)


FINANCIALS = [
    {"q": "Q1'24", "revenue": 100, "earnings": 30, "margin": 30.0},
    {"q": "Q2'24", "revenue": 105, "earnings": 31, "margin": 29.5},
    {"q": "Q3'24", "revenue": 108, "earnings": 33, "margin": 30.5},
    {"q": "Q4'24", "revenue": 112, "earnings": 35, "margin": 31.2},
    {"q": "Q1'25", "revenue": 115, "earnings": 36, "margin": 31.3},
    {"q": "Q2'25", "revenue": 118, "earnings": 37, "margin": 31.4},
]


class StubLLMProvider:
    def __init__(self, text: str = "Revenue grew this quarter, roughly in line with its recent trend."):
        self.text = text
        self.calls = 0

    def generate_verdict(self, payload):
        self.calls += 1
        return self.text


class StubTelegramBot:
    def __init__(self):
        self.sent = []

    def send_to_watchers(self, db, ticker, text, chat_ids):
        self.sent.append((ticker, text))

        class _Result:
            status = "sent"

        return [_Result()]


def _mock_sectors_routes():
    respx.get(f"{BASE_URL}/company/get_quarterly_financial_dates/BBRI/").mock(
        return_value=httpx.Response(200, json={"dates": ["Q1'24", "Q2'24", "Q3'24", "Q4'24", "Q1'25", "Q2'25"]})
    )
    respx.get(f"{BASE_URL}/financials/quarterly/BBRI/").mock(
        return_value=httpx.Response(200, json={"financials": FINANCIALS})
    )
    respx.get(f"{BASE_URL}/companies/top-growth/").mock(
        return_value=httpx.Response(200, json={"companies": [
            {"ticker": "BBCA", "growth": 0.05},
            {"ticker": "BMRI", "growth": 0.08},
            {"ticker": "BBTN", "growth": 0.02},
        ]})
    )


@respx.mock
def test_run_for_ticker_end_to_end(tmp_path):
    _mock_sectors_routes()

    db = Database(path=str(tmp_path / "test.db"))
    db.add_ticker("BBRI", "Banks")

    client = SectorsClient(api_key="test-key", base_url=BASE_URL)
    llm = StubLLMProvider()
    bot = StubTelegramBot()

    result = run_for_ticker(
        ticker="BBRI", sector="Banks", db=db, sectors_client=client,
        llm_primary=cast(LLMProvider, llm), telegram_bot=bot,
    )

    assert result.status == "new_verdict"
    assert result.card is not None
    assert result.card["ticker"] == "BBRI"
    assert result.card["quarter"] == "Q2'25"
    assert result.card["direction"] in {"above", "below", "inline"}
    assert "DISCLAIMER" in result.card["verdict"]
    assert bot.sent, "verdict should have been delivered"

    # persisted state should now reflect this run
    assert p.period == "Q2'25" if (p := db.get_last_seen("BBRI")) is not None else False
    assert db.get_verdict("BBRI", "Q2'25") is not None


@respx.mock
def test_run_for_ticker_is_idempotent_per_quarter(tmp_path):
    _mock_sectors_routes()

    db = Database(path=str(tmp_path / "test.db"))
    db.add_ticker("BBRI", "Banks")

    client = SectorsClient(api_key="test-key", base_url=BASE_URL)
    llm = StubLLMProvider()
    bot = StubTelegramBot()

    first = run_for_ticker(ticker="BBRI", sector="Banks", db=db, sectors_client=client, llm_primary=cast(LLMProvider, llm), telegram_bot=bot)
    second = run_for_ticker(ticker="BBRI", sector="Banks", db=db, sectors_client=client, llm_primary=cast(LLMProvider, llm), telegram_bot=bot)

    assert first.status == "new_verdict"
    assert second.status == "stale"
    assert len(bot.sent) == 1  # no duplicate delivery on re-check


@respx.mock
def test_run_for_ticker_survives_missing_financials(tmp_path):
    respx.get(f"{BASE_URL}/company/get_quarterly_financial_dates/BBRI/").mock(
        return_value=httpx.Response(200, json={"dates": ["Q1'25", "Q2'25"]})
    )
    respx.get(f"{BASE_URL}/financials/quarterly/BBRI/").mock(return_value=httpx.Response(500))

    db = Database(path=str(tmp_path / "test.db"))
    db.add_ticker("BBRI", "Banks")
    client = SectorsClient(api_key="test-key", base_url=BASE_URL, max_retries=1)

    result = run_for_ticker(
        ticker="BBRI", sector="Banks", db=db, sectors_client=client,
        llm_primary=cast(LLMProvider, StubLLMProvider()), telegram_bot=StubTelegramBot(),
    )

    assert result.status == "error" 
    assert result.error is None or result.error.stage == "compute"

