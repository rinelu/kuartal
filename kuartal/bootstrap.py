"""
Centralizes provider construction from settings.

All entrypoints should build Gemini, OpenAI-compatible, and Telegram
providers through this module so provider setup and enable/disable logic
stay consistent everywhere.
"""

from __future__ import annotations

import logging

from kuartal.config import settings
from kuartal.llm.base import LLMProvider

logger = logging.getLogger("kuartal.bootstrap")

def build_llm_primary() -> LLMProvider | None:
    if not settings.pipeline_enable_llm: return None

    from kuartal.llm.gemini_provider import GeminiProvider
    return GeminiProvider()


def build_llm_fallback() -> LLMProvider | None:
    if settings.llm_fallback_provider == "none": return None

    from kuartal.llm.fallback_provider import OpenAICompatibleProvider
    return OpenAICompatibleProvider()


def build_telegram_bot():
    if not settings.pipeline_enable_delivery:
        return None

    if not settings.telegram_bot_token:
        logger.warning(
            "Delivery is enabled, but telegram_bot_token is missing. "
            "Delivery will fail on the first send."
        )

    from kuartal.delivery.telegram_bot import TelegramBot
    return TelegramBot()


def build_all() -> tuple[LLMProvider | None, LLMProvider | None, object | None]:
    return build_llm_primary(), build_llm_fallback(), build_telegram_bot()
