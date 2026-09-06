"""
Typed interface for the Sectors endpoints used by Kuartal.

Provides one function for each required endpoint, with endpoint-specific
request and response handling kept separate from the underlying API client.
"""

from __future__ import annotations
from typing import Any
from kuartal.pipeline.compute import QuarterFinancial
from kuartal.sectors.client import SectorsClient
from kuartal.sectors.normalize import (
    normalize_daily_prices,
    normalize_financials,
    normalize_growth_rankings,
    normalize_ticker,
)

# Fields required by the pipeline for each endpoint response.
# Kept here as the source of truth for contract tests.
REQUIRED_FIELDS = {
    "quarterly_financial_dates": {"dates"},
    "quarterly_financials":      {"financials"},
    "top_growth":                {"companies"},
    "company_report":            {"ticker", "sector"},
    "daily_prices":              {"prices"},
}

def get_quarterly_financial_dates(client: SectorsClient, ticker: str) -> list[str]:
    """Trigger stage: retrieves the quarters with available reports for ticker."""

    data = client.get(f"/company/get_quarterly_financial_dates/{normalize_ticker(ticker)}/")
    return data.get("dates", [])

def get_quarterly_financials(client: SectorsClient, ticker: str) -> list[QuarterFinancial]:
    """Own-trend input: retrieves trailing quarterly revenue and earnings history."""

    data = client.get(f"/financials/quarterly/{normalize_ticker(ticker)}/")
    return normalize_financials(data.get("financials", []))

def get_top_growth(client: SectorsClient, sector: str) -> list[dict[str, Any]]:
    """Sector-relative input: retrieves growth rankings for peers in `sector`."""

    data = client.get("/companies/top-growth/", params={ "sector": sector })
    return normalize_growth_rankings(data.get("companies", []))

def get_company_report(client: SectorsClient, ticker: str) -> dict[str, Any]:
    """Report-card display context (name, sector, overview, valuation)."""

    return client.get(f"/company/report/{normalize_ticker(ticker)}/", params={ "sections": "overview,valuation" })

def get_daily_prices(
    client: SectorsClient,
    ticker: str,
    start: str | None = None,
    end: str | None = None,
) -> list[dict[str, Any]]:
    """Backtest-only input: fetches daily closing prices for ticker.

    Not used by the live pipeline. It exists only for backtest/data_fetch.py
    to compare quarterly financials with subsequent price performance.

    `start` and `end` are optional YYYY-MM-DD bounds.
    """

    params: dict[str, Any] = {}
    if start: params["start"] = start
    if end:   params["end"]   = end

    data = client.get(f"/company/daily-price/{normalize_ticker(ticker)}/", params=params or None)
    return normalize_daily_prices(data.get("prices", []))
