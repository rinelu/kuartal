"""
End-to-end pipeline: trigger -> compute -> verdict -> deliver.

Stage and ticker failures are recorded and skipped, so one failure never
stops the watchlist. Stages can be disabled via config.py settings
(pipeline_enable_llm, pipeline_enable_delivery) for compute-only runs.

Successful runs return the CompanyCard contract and mirrored in
kuartal/api/schemas.py.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from kuartal.config import settings
from kuartal.llm import service as llm_service
from kuartal.llm.base import LLMProvider
from kuartal.pipeline import compute, status as pipeline_status
from kuartal.pipeline.verdict import build_verdict_payload
from kuartal.sectors import endpoints
from kuartal.sectors.client import SectorsAPIError, SectorsClient, SectorsRateLimitError
from kuartal.storage.db import Database
from kuartal.storage.models import LastSeenReport, VerdictLogEntry

logger = logging.getLogger("kuartal.pipeline.run")

@dataclass
class StageError:
    stage: str  # "trigger" | "compute" | "verdict" | "deliver" | "persist"
    error: str

@dataclass
class PipelineResult:
    ticker: str
    status: str  # "new_verdict" | "stale" | "error"
    card: dict | None = None
    error: StageError | None = None

def _elapsed_label(start: float) -> str:
    seconds = time.monotonic() - start
    minutes, remainder = divmod(int(seconds), 60)
    return f"{minutes}m {remainder}s"

def run_for_ticker(
    ticker:         str,
    sector:         str,
    db:             Database,
    sectors_client: SectorsClient,
    llm_primary:    LLMProvider | None    = None,
    llm_fallback:   LLMProvider | None    = None,
    telegram_bot                          = None,
    chat_ids:       dict[str, str] | None = None,
    name:           str | None            = None,
    force:          bool                  = False,
) -> PipelineResult:
    """
    Run the full pipeline for one ticker.

    If the latest quarter matches `last_seen_report`, skip the run unless
    `force` is set. This keeps each ticker from running more than once per
    quarter, even when called on every poll cycle.
    """

    start = time.monotonic()
    pipeline_status.reset(ticker)
    
    # --- trigger stage -------------------------------------------------
    pipeline_status.mark(ticker, "report detected", "in_progress")
    try:
        dates = endpoints.get_quarterly_financial_dates(sectors_client, ticker)
    except (SectorsAPIError, SectorsRateLimitError) as exc:
        logger.warning("trigger stage failed ticker=%s error=%s", ticker, exc)
        pipeline_status.mark(ticker, "report detected", "failed")
        return PipelineResult(ticker=ticker, status="error", error=StageError("trigger", str(exc)))
    
    if not dates:
        pipeline_status.mark(ticker, "report detected", "done")
        return PipelineResult(ticker=ticker, status="stale")

    latest_period = dates[-1]
    last_seen     = db.get_last_seen(ticker)
    if not force and last_seen is not None and last_seen.period == latest_period:
        pipeline_status.mark(ticker, "report detected", "done")
        return PipelineResult(ticker=ticker, status="stale")

    pipeline_status.mark(ticker, "report detected", "done")

    # --- compute stage ---------------------------------------------------
    pipeline_status.mark(ticker, "history read", "in_progress")
    try:
        financials     = endpoints.get_quarterly_financials(sectors_client, ticker)
        own_trend      = compute.own_trend(financials)
        margins        = compute.margin_series(financials)
        this_growth    = compute.yoy_growth(financials)
        own_avg_growth = compute.own_avg_growth_4q(financials)
        pipeline_status.mark(ticker, "history read", "done")

        pipeline_status.mark(ticker, "sector ranked", "in_progress")
        peers = endpoints.get_top_growth(sectors_client, sector)
        peer_growths = [p["growth"] for p in peers if p.get("ticker") != ticker]
        percentile, peer_count = compute.sector_percentile(this_growth or 0.0, peer_growths)
        trend_direction = compute.direction(this_growth or 0.0, own_avg_growth)
        pipeline_status.mark(ticker, "sector ranked", "done")

    except (SectorsAPIError, SectorsRateLimitError) as exc:
        logger.warning("compute stage failed ticker=%s error=%s", ticker, exc)
        pipeline_status.mark(ticker, "history read", "failed")
        pipeline_status.mark(ticker, "sector ranked", "failed")
        return PipelineResult(ticker=ticker, status="error", error=StageError("compute", str(exc)))

    except Exception as exc:
        logger.exception("compute stage raised unexpectedly ticker=%s", ticker)
        pipeline_status.mark(ticker, "history read", "failed")
        pipeline_status.mark(ticker, "sector ranked", "failed")
        return PipelineResult(ticker=ticker, status="error", error=StageError("compute", str(exc)))

    # --- verdict stage -----------------------------------------------
    pipeline_status.mark(ticker, "verdict generated", "in_progress")
    verdict_text: str
    if settings.pipeline_enable_llm and llm_primary is not None:
        try:
            payload = build_verdict_payload(
                ticker=ticker,
                period=latest_period,
                revenue_growth_yoy=this_growth or 0.0,
                own_avg_growth_4q=own_avg_growth or 0.0,
                sector=sector,
                sector_percentile=percentile,
            )
            verdict_text = llm_service.generate_verdict_text(payload, llm_primary, llm_fallback)

        except Exception as exc:
            logger.warning("verdict stage failed ticker=%s error=%s", ticker, exc)
            pipeline_status.mark(ticker, "verdict generated", "failed")
            return PipelineResult(ticker=ticker, status="error", error=StageError("verdict", str(exc)))
    else:
        from kuartal.llm.service import _template_sentence
        from kuartal.pipeline.verdict import DISCLAIMER

        payload = build_verdict_payload(
            ticker=ticker,
            period=latest_period,
            revenue_growth_yoy=this_growth or 0.0,
            own_avg_growth_4q=own_avg_growth or 0.0,
            sector=sector,
            sector_percentile=percentile,
        )
        verdict_text = f"{_template_sentence(payload)} {DISCLAIMER}"
    pipeline_status.mark(ticker, "verdict generated", "done")

    # --- deliver stage -------------------------------------------------
    delivered_at: str | None = None
    opened = False
    delivery_status = "not_attempted"
    if settings.pipeline_enable_delivery and telegram_bot is not None:
        try:
            results = telegram_bot.send_to_watchers(db, ticker, verdict_text, chat_ids or {})
            if any(r.status == "sent" for r in results):
                delivered_at = datetime.now(timezone.utc).isoformat()
                delivery_status = "sent"
            elif results:
                delivery_status = "failed"

        except Exception as exc:
            logger.error("deliver stage failed ticker=%s error=%s", ticker, exc)
            delivery_status = "failed"

    # --- persist stage ---------------------------------------------------
    time_to_verdict_label = _elapsed_label(start)
    try:
        db.set_last_seen(LastSeenReport(ticker=ticker, period=latest_period, seen_at=datetime.now(timezone.utc)))
        db.add_verdict(
            VerdictLogEntry(
                ticker=ticker,
                quarter=latest_period,
                verdict=verdict_text,
                direction=trend_direction,
                percentile=percentile,
                delivered_at=datetime.fromisoformat(delivered_at) if delivered_at else None,
                opened=opened,
                time_to_verdict=time_to_verdict_label,
                delivery_status=delivery_status,
            )
        )
    except Exception as exc:
        logger.error("persist stage failed ticker=%s error=%s", ticker, exc)
        return PipelineResult(ticker=ticker, status="error", error=StageError("persist", str(exc)))
    
    card = {
        "ticker":           ticker,
        "name":             name or ticker,
        "sector":           sector,
        "quarter":          latest_period,
        "status":           "new",
        "verdict":          verdict_text,
        "direction":        trend_direction,
        "ownTrend":         own_trend,
        "ownAvgGrowth":     own_avg_growth or 0.0,
        "thisGrowth":       this_growth or 0.0,
        "sectorPercentile": percentile,
        "sectorPeerCount":  peer_count,
        "margin":           margins,
        "channel":          "Telegram",
        "lastSent":         delivered_at or "",
        "opened":           opened,
        "timeToVerdict":    time_to_verdict_label,
    }
    return PipelineResult(ticker=ticker, status="new_verdict", card=card)

def run_watchlist(
    db: Database,
    sectors_client: SectorsClient,
    llm_primary: LLMProvider | None = None,
    llm_fallback: LLMProvider | None = None,
    telegram_bot=None,
    chat_ids: dict[str, str] | None = None,
) -> list[PipelineResult]:
    """Run the pipeline for each unique ticker on the watchlist.

    A failure in one ticker must never stop the remaining tickers from running.
    """

    results: list[PipelineResult] = []
    for watch in db.list_watchlist():
        try:
            result = run_for_ticker(
                ticker=watch.ticker,
                sector=watch.sector,
                db=db,
                sectors_client=sectors_client,
                llm_primary=llm_primary,
                llm_fallback=llm_fallback,
                telegram_bot=telegram_bot,
                chat_ids=chat_ids
            )

        except Exception as exc:  # last-resort guard, see docstring
            logger.exception("unexpected failure running pipeline for ticker=%s", watch.ticker)
            result = PipelineResult(ticker=watch.ticker, status="error", error=StageError("unexpected", str(exc)))

        results.append(result)

    return results
