from __future__ import annotations
from kuartal import bootstrap

def test_build_llm_primary_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr("kuartal.bootstrap.settings.pipeline_enable_llm", False)
    assert bootstrap.build_llm_primary() is None

def test_build_llm_primary_returns_provider_when_enabled(monkeypatch):
    monkeypatch.setattr("kuartal.bootstrap.settings.pipeline_enable_llm", True)
    provider = bootstrap.build_llm_primary()
    assert provider is not None
    assert type(provider).__name__ == "GeminiProvider"

def test_build_llm_fallback_returns_none_when_provider_is_none(monkeypatch):
    monkeypatch.setattr("kuartal.bootstrap.settings.llm_fallback_provider", "none")
    assert bootstrap.build_llm_fallback() is None

def test_build_llm_fallback_returns_provider_when_configured(monkeypatch):
    monkeypatch.setattr("kuartal.bootstrap.settings.llm_fallback_provider", "openrouter")
    provider = bootstrap.build_llm_fallback()
    assert provider is not None
    assert type(provider).__name__ == "OpenAICompatibleProvider"

def test_build_telegram_bot_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr("kuartal.bootstrap.settings.pipeline_enable_delivery", False)
    assert bootstrap.build_telegram_bot() is None

def test_build_telegram_bot_returns_bot_when_enabled(monkeypatch):
    monkeypatch.setattr("kuartal.bootstrap.settings.pipeline_enable_delivery", True)
    bot = bootstrap.build_telegram_bot()
    assert bot is not None
    assert type(bot).__name__ == "TelegramBot"

def test_build_telegram_bot_warns_when_token_missing(monkeypatch, caplog):
    monkeypatch.setattr("kuartal.bootstrap.settings.pipeline_enable_delivery", True)
    monkeypatch.setattr("kuartal.bootstrap.settings.telegram_bot_token", "")

    with caplog.at_level("WARNING", logger="kuartal.bootstrap"):
        bootstrap.build_telegram_bot()

    assert any("telegram_bot_token is missing" in record.message for record in caplog.records)

def test_build_all_respects_all_toggles(monkeypatch):
    monkeypatch.setattr("kuartal.bootstrap.settings.pipeline_enable_llm", False)
    monkeypatch.setattr("kuartal.bootstrap.settings.llm_fallback_provider", "none")
    monkeypatch.setattr("kuartal.bootstrap.settings.pipeline_enable_delivery", False)

    llm_primary, llm_fallback, telegram_bot = bootstrap.build_all()

    assert llm_primary is None
    assert llm_fallback is None
    assert telegram_bot is None
