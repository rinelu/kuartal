"""
Generate a safe, disclaimed verdict for the pipeline.

This service handles the LLM providers, fallback logic, output checks,
and disclaimer so pipeline/run.py only needs one call and never gets
a raw model response.
"""

from __future__ import annotations

import logging

from kuartal.config import settings
from kuartal.llm import filters
from kuartal.llm.base import LLMProvider, LLMProviderError, LLMRateLimitError
from kuartal.pipeline.verdict import DISCLAIMER, VerdictPayload

logger = logging.getLogger("kuartal.llm.service")

def _template_sentence(payload: VerdictPayload) -> str:
    """
    Build a deterministic, filter-safe sentence when the LLM output can't pass
    after a retry. Uses only computed values and adds no new claims.
    """

    return (
        f"{payload['ticker']}'s revenue grew {payload['revenue_growth_yoy']:.0%} "
        f"in {payload['period']}, versus its own {payload['own_avg_growth_4q']:.0%} "
        f"average over the trailing four quarters, at around the "
        f"{payload['sector_percentile']}th percentile of the {payload['sector']} sector."
    )

def _generate_once(primary: LLMProvider, fallback: LLMProvider | None, payload: VerdictPayload) -> str:
    try:
        return primary.generate_verdict(payload)
    except LLMRateLimitError:
        if fallback is None: raise

        logger.warning("primary LLM provider rate-limited, using fallback ticker=%s", payload["ticker"])
        return fallback.generate_verdict(payload)

def generate_verdict_text(
    payload: VerdictPayload,
    primary: LLMProvider,
    fallback: LLMProvider | None = None,
) -> str:
    text: str | None = None
    last_error: Exception | None = None

    for attempt in range(2):
        try:
            candidate = _generate_once(primary, fallback, payload)
        except (LLMProviderError, LLMRateLimitError) as exc:
            last_error = exc
            logger.warning("LLM generation failed attempt=%s ticker=%s error=%s", attempt, payload["ticker"], exc)
            continue

        if filters.passes_all_checks(candidate):
            text = candidate
            break

        logger.warning("LLM output failed advice-language/length gate, regenerating ticker=%s", payload["ticker"])

    if text is None:
        logger.warning( "Falling back to template sentence for ticker=%s (last_error=%s)", payload["ticker"], last_error)
        text = _template_sentence(payload)

    return f"{text} {DISCLAIMER}"
