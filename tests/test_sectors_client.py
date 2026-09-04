"""Mocks HTTP requests with respx to avoid calls to the live Sectors API."""

import httpx
import pytest
import respx

from kuartal.sectors.client import SectorsAPIError, SectorsClient

@respx.mock
def test_get_returns_json_on_success():
    respx.get("https://api.sectors.app/company/report/BBRI/").mock(
        return_value=httpx.Response(200, json={"ticker": "BBRI"})
    )
    client = SectorsClient(api_key="test-key", base_url="https://api.sectors.app")
    result = client.get("/company/report/BBRI/")
    assert result == {"ticker": "BBRI"}

@respx.mock
def test_get_retries_on_5xx_then_raises():
    route = respx.get("https://api.sectors.app/company/report/BBRI/").mock(
        return_value=httpx.Response(500)
    )
    client = SectorsClient(api_key="test-key", base_url="https://api.sectors.app", max_retries=2)
    with pytest.raises(SectorsAPIError):
        client.get("/company/report/BBRI/")

    assert route.call_count == 2

@respx.mock
def test_get_does_not_retry_on_4xx():
    route = respx.get("https://api.sectors.app/company/report/BAD/").mock(
        return_value=httpx.Response(404)
    )
    client = SectorsClient(api_key="test-key", base_url="https://api.sectors.app", max_retries=3)
    with pytest.raises(SectorsAPIError):
        client.get("/company/report/BAD/")

    assert route.call_count == 1
