"""
Polling loop for new-quarter detection.

`pipeline/run.run_for_ticker` handles the quarter check and idempotency.
This module only schedules watchlist checks, logs each cycle, and keeps
the loop running if a cycle fails.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from kuartal.config import settings
from kuartal.llm.base import LLMProvider
from kuartal.pipeline.run import PipelineResult, run_watchlist
from kuartal.sectors.client import SectorsClient
from kuartal.storage.db import Database

logger = logging.getLogger("kuartal.scheduler")
logging.basicConfig(level=logging.INFO)

def retry_pending_deliveries(
    db: Database,
    telegram_bot,
    chat_ids: dict[str, str] | None = None,
) -> int:
    """
    Retry failed verdict deliveries.

    Returns the number of successfully retried deliveries.
    """

    if telegram_bot is None: return 0

    succeeded = 0
    for entry in db.pending_redeliveries():
        try:
            results = telegram_bot.send_to_watchers(db, entry.ticker, entry.verdict, chat_ids or {})
        except Exception:
            logger.exception("redelivery attempt raised unexpectedly ticker=%s quarter=%s", entry.ticker, entry.quarter)
            continue

        if any(r.status == "sent" for r in results):
            db.mark_delivery_status(entry.ticker, entry.quarter, "sent", datetime.now(timezone.utc))
            succeeded += 1
            logger.info("redelivery succeeded ticker=%s quarter=%s", entry.ticker, entry.quarter)
        else:
            logger.warning("redelivery still failing ticker=%s quarter=%s", entry.ticker, entry.quarter)

    return succeeded

def run_cycle(
    db: Database,
    sectors_client: SectorsClient,
    llm_primary: LLMProvider | None = None,
    llm_fallback: LLMProvider | None = None,
    telegram_bot=None,
    chat_ids: dict[str, str] | None = None,
) -> list[PipelineResult]:
    """
    Run one check cycle for the watchlist and log each ticker's result,
    including when it was checked. Used for the dashboard's time-to-verdict
    metric.
    """

    retry_pending_deliveries(db, telegram_bot, chat_ids)

    checked_at = datetime.now(timezone.utc).isoformat()
    results = run_watchlist(
        db=db,
        sectors_client=sectors_client,
        llm_primary=llm_primary,
        llm_fallback=llm_fallback,
        telegram_bot=telegram_bot,
        chat_ids=chat_ids
    )

    for result in results:
        logger.info(
            "check_cycle ticker=%s checked_at=%s result=%s%s",
            result.ticker, checked_at, result.status,
            f" stage={result.error.stage} error={result.error.error}" if result.error else ""
        )

    return results


def run_forever(
    db: Database,
    sectors_client: SectorsClient,
    llm_primary: LLMProvider | None = None,
    llm_fallback: LLMProvider | None = None,
    telegram_bot=None,
    chat_ids: dict[str, str] | None = None,
    poll_interval_seconds: int | None = None,
) -> None:
    """
    Poll the watchlist continuously at the configured interval.

    If an unexpected cycle error occurs, log it and retry after a short
    backoff instead of stopping the scheduler.
    """

    interval = poll_interval_seconds or settings.poll_interval_seconds
    while True:
        try:
            run_cycle(
                db=db,
                sectors_client=sectors_client,
                llm_primary=llm_primary,
                llm_fallback=llm_fallback,
                telegram_bot=telegram_bot,
                chat_ids=chat_ids
            )

        except Exception:
            logger.exception("scheduler cycle crashed, restarting after backoff")
            time.sleep(settings.scheduler_restart_backoff_seconds)
            continue

        time.sleep(interval)

if __name__ == "__main__":
    from kuartal.bootstrap import build_all

    _db = Database()
    _client = SectorsClient()
    _llm_primary, _llm_fallback, _telegram_bot = build_all()
    run_forever(
        db=_db,
        sectors_client=_client,
        llm_primary=_llm_primary,
        llm_fallback=_llm_fallback,
        telegram_bot=_telegram_bot,
    )
