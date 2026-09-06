from __future__ import annotations

import httpx
import pytest
import respx

from kuartal.llm.base import LLMProviderError, LLMRateLimitError
from kuartal.llm.gemini_provider import GEMINI_BASE_URL, GeminiProvider
from kuartal.pipeline.verdict import build_verdict_payload

PAYLOAD = build_verdict_payload(
    ticker="BBRI", period="Q2'25", revenue_growth_yoy=0.09,
    own_avg_growth_4q=0.15, sector="Banks", sector_percentile=65,
)

def _provider(**kwargs) -> GeminiProvider:
    return GeminiProvider(api_key="test-key", model="gemini-1.5-flash", **kwargs)

@respx.mock
def test_generate_verdict_happy_path():
    url = f"{GEMINI_BASE_URL}/gemini-1.5-flash:generateContent"
    respx.post(url).mock(
        return_value=httpx.Response(200, json={
            "candidates": [{ "content": { "parts": [{ "text": "Revenue grew 9% this quarter." }] } }]
        })
    )

    text = _provider().generate_verdict(PAYLOAD)
    assert text == "Revenue grew 9% this quarter."

@respx.mock
def test_generate_verdict_sends_expected_request_shape():
    url = f"{GEMINI_BASE_URL}/gemini-1.5-flash:generateContent"
    route = respx.post(url).mock(
        return_value=httpx.Response(200, json={
            "candidates": [{ "content": { "parts": [{ "text": "ok" }] } }]
        })
    )

    _provider().generate_verdict(PAYLOAD)

    request = route.calls.last.request
    assert request.url.params["key"] == "test-key"
    import json as _json
    sent = _json.loads(route.calls.last.request.content)
    assert "system_instruction" in sent
    assert "BBRI" in sent["contents"][0]["parts"][0]["text"]

@respx.mock
def test_generate_verdict_retries_then_succeeds_on_429(monkeypatch):
    monkeypatch.setattr("kuartal.llm.gemini_provider.time.sleep", lambda _: None)
    url = f"{GEMINI_BASE_URL}/gemini-1.5-flash:generateContent"
    route = respx.post(url).mock(side_effect=[
        httpx.Response(429),
        httpx.Response(200, json={ "candidates": [{ "content": { "parts": [{ "text": "ok now"}] } }] }),
    ])

    text = _provider(max_retries=3).generate_verdict(PAYLOAD)

    assert text == "ok now"
    assert route.call_count == 2

@respx.mock
def test_generate_verdict_raises_rate_limit_error_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr("kuartal.llm.gemini_provider.time.sleep", lambda _: None)
    url = f"{GEMINI_BASE_URL}/gemini-1.5-flash:generateContent"
    respx.post(url).mock(return_value=httpx.Response(429))

    with pytest.raises(LLMRateLimitError):
        _provider(max_retries=2).generate_verdict(PAYLOAD)

@respx.mock
def test_generate_verdict_raises_provider_error_on_4xx():
    url = f"{GEMINI_BASE_URL}/gemini-1.5-flash:generateContent"
    respx.post(url).mock(return_value=httpx.Response(400, json={ "error": "bad request" }))

    with pytest.raises(LLMProviderError):
        _provider(max_retries=2).generate_verdict(PAYLOAD)

@respx.mock
def test_generate_verdict_raises_provider_error_on_malformed_response():
    url = f"{GEMINI_BASE_URL}/gemini-1.5-flash:generateContent"
    respx.post(url).mock(return_value=httpx.Response(200, json={ "unexpected": "shape" }))

    with pytest.raises(LLMProviderError):
        _provider(max_retries=1).generate_verdict(PAYLOAD)
