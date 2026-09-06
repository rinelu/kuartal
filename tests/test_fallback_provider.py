from __future__ import annotations

import httpx
import pytest
import respx

from kuartal.llm.base import LLMProviderError, LLMRateLimitError
from kuartal.llm.fallback_provider import FallbackProviderUnavailable, OpenAICompatibleProvider
from kuartal.pipeline.verdict import build_verdict_payload

PAYLOAD = build_verdict_payload(
    ticker="BBRI", period="Q2'25", revenue_growth_yoy=0.09,
    own_avg_growth_4q=0.15, sector="Banks", sector_percentile=65,
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def _provider(**kwargs) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(provider_name="openrouter", api_key="test-key", model="test-model", **kwargs)

@respx.mock
def test_generate_verdict_happy_path():
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json={
            "choices": [{ "message": { "content": "Revenue grew 9% this quarter." } }]
        })
    )

    text = _provider().generate_verdict(PAYLOAD)
    assert text == "Revenue grew 9% this quarter."

@respx.mock
def test_generate_verdict_sends_bearer_auth_and_model():
    route = respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json={
            "choices": [{ "message": { "content": "ok" } }]
        })
    )

    _provider().generate_verdict(PAYLOAD)

    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer test-key"
    import json as _json
    sent = _json.loads(request.content)
    assert sent["model"] == "test-model"
    assert "BBRI" in sent["messages"][1]["content"]

def test_groq_uses_its_own_base_url():
    provider = OpenAICompatibleProvider(provider_name="groq", api_key="k", model="m")
    assert provider.base_url == GROQ_URL

def test_unknown_provider_name_raises():
    with pytest.raises(FallbackProviderUnavailable):
        OpenAICompatibleProvider(provider_name="not-a-real-provider")

@respx.mock
def test_generate_verdict_retries_then_succeeds_on_429(monkeypatch):
    monkeypatch.setattr("kuartal.llm.fallback_provider.time.sleep", lambda _: None)
    route = respx.post(OPENROUTER_URL).mock(side_effect=[
        httpx.Response(429),
        httpx.Response(200, json={"choices": [{"message": {"content": "ok now"}}]}),
    ])

    text = _provider(max_retries=3).generate_verdict(PAYLOAD)

    assert text == "ok now"
    assert route.call_count == 2

@respx.mock
def test_generate_verdict_raises_rate_limit_error_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr("kuartal.llm.fallback_provider.time.sleep", lambda _: None)
    respx.post(OPENROUTER_URL).mock(return_value=httpx.Response(429))

    with pytest.raises(LLMRateLimitError):
        _provider(max_retries=2).generate_verdict(PAYLOAD)

@respx.mock
def test_generate_verdict_raises_provider_error_on_4xx():
    respx.post(OPENROUTER_URL).mock(return_value=httpx.Response(401, json={"error": "bad key"}))

    with pytest.raises(LLMProviderError):
        _provider(max_retries=2).generate_verdict(PAYLOAD)

@respx.mock
def test_generate_verdict_raises_provider_error_on_malformed_response():
    respx.post(OPENROUTER_URL).mock(return_value=httpx.Response(200, json={"unexpected": "shape"}))

    with pytest.raises(LLMProviderError):
        _provider(max_retries=1).generate_verdict(PAYLOAD)
