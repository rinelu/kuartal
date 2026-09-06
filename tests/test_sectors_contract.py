"""
Contract tests for the Sectors endpoints.

These assert that each endpoint's (mocked) response actually contains the
fields `pipeline/compute.py` and `pipeline/run.py` depend on, catching
upstream shape drift before it silently breaks the pipeline. This is
distinct from `test_sectors_client.py`, which only covers the HTTP/retry
behavior of the underlying client.
"""

import httpx
import respx

from kuartal.sectors import endpoints
from kuartal.sectors.client import SectorsClient

BASE_URL = "https://api.sectors.app"


def _client() -> SectorsClient:
    return SectorsClient(api_key="test-key", base_url=BASE_URL)


@respx.mock
def test_quarterly_financial_dates_contract():
    respx.get(f"{BASE_URL}/company/get_quarterly_financial_dates/BBRI/").mock(
        return_value=httpx.Response(200, json={"dates": ["2025Q1", "2025Q2"]})
    )
    dates = endpoints.get_quarterly_financial_dates(_client(), "BBRI")

    assert isinstance(dates, list)
    assert all(isinstance(d, str) for d in dates)


@respx.mock
def test_quarterly_financials_contract():
    respx.get(f"{BASE_URL}/financials/quarterly/BBRI/").mock(
        return_value=httpx.Response(200, json={
            "financials": [
                {"q": "Q1'25", "revenue": 100, "earnings": 20, "margin": 20.0},
                {"q": "Q2'25", "revenue": 110, "earnings": 22, "margin": 20.0},
            ]
        })
    )
    financials = endpoints.get_quarterly_financials(_client(), "BBRI")

    assert financials
    for entry in financials:
        assert {"q", "revenue", "earnings", "margin"} <= entry.keys()
        assert isinstance(entry["revenue"], float)
        assert isinstance(entry["earnings"], float)


@respx.mock
def test_top_growth_contract():
    respx.get(f"{BASE_URL}/companies/top-growth/").mock(
        return_value=httpx.Response(200, json={
            "companies": [{"ticker": "BBRI", "growth": 0.09}, {"ticker": "BBTN", "growth": 0.04}]
        })
    )
    rankings = endpoints.get_top_growth(_client(), "Banks")

    assert rankings
    for entry in rankings:
        assert {"ticker", "growth"} <= entry.keys()


@respx.mock
def test_company_report_contract():
    respx.get(f"{BASE_URL}/company/report/BBRI/").mock(
        return_value=httpx.Response(200, json={
            "ticker": "BBRI", "sector": "Banks", "overview": {}, "valuation": {}
        })
    )
    report = endpoints.get_company_report(_client(), "BBRI")

    assert endpoints.REQUIRED_FIELDS["company_report"] <= report.keys()


@respx.mock
def test_quarterly_financials_missing_fields_are_caught():
    """A malformed upstream response (missing the `financials` key entirely)
    should surface as an empty list, not a KeyError, so the pipeline can
    treat it as "no data this cycle" rather than crashing."""

    respx.get(f"{BASE_URL}/financials/quarterly/BBRI/").mock(
        return_value=httpx.Response(200, json={})
    )
    financials = endpoints.get_quarterly_financials(_client(), "BBRI")

    assert financials == []


@respx.mock
def test_daily_prices_contract():
    respx.get(f"{BASE_URL}/company/daily-price/BBRI/").mock(
        return_value=httpx.Response(200, json={
            "prices": [
                {"date": "2025-01-01", "close": 4500},
                {"date": "2025-01-02", "close": "4,520.5"},
            ]
        })
    )
    prices = endpoints.get_daily_prices(_client(), "BBRI")

    assert prices
    for entry in prices:
        assert {"date", "close"} <= entry.keys()
        assert isinstance(entry["close"], float)


@respx.mock
def test_daily_prices_passes_start_end_params():
    route = respx.get(f"{BASE_URL}/company/daily-price/BBRI/").mock(
        return_value=httpx.Response(200, json={"prices": []})
    )
    endpoints.get_daily_prices(_client(), "BBRI", start="2025-01-01", end="2025-03-31")

    assert route.called
    request = route.calls.last.request
    assert request.url.params["start"] == "2025-01-01"
    assert request.url.params["end"] == "2025-03-31"
