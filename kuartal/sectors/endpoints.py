"""
Typed interface for the Sectors endpoints used by Kuartal.

Provides one function for each required endpoint, with endpoint-specific
request and response handling kept separate from the underlying API client.
"""

from __future__ import annotations
from typing import Any
from kuartal.pipeline.compute import QuarterFinancial
from kuartal.sectors.client import SectorsClient

def get_quarterly_financial_dates(client: SectorsClient, ticker: str) -> list[str]:
    """Trigger stage: retrieves the quarters with available reports for ticker."""

    data = client.get(f"/company/get_quarterly_financial_dates/{ticker}/")
    return data.get("dates", [])

def get_quarterly_financials(client: SectorsClient, ticker: str) -> list[QuarterFinancial]:
    """Own-trend input: retrieves trailing quarterly revenue and earnings history."""

    data = client.get(f"/financials/quarterly/{ticker}/")
    return data.get("financials", [])


def get_top_growth(client: SectorsClient, sector: str) -> list[dict[str, Any]]:
    """Sector-relative input: retrieves growth rankings for peers in `sector`."""

    data = client.get("/companies/top-growth/", params={ "sector": sector })
    return data.get("companies", [])


def get_company_report(client: SectorsClient, ticker: str) -> dict[str, Any]:
    """Report-card display context (name, sector, overview, valuation)."""

    return client.get(f"/company/report/{ticker}/",
                      params={ "sections": "overview,valuation" })
