"""
Thin API read layer over storage/db.py.

Exposes the dashboard endpoints defined in dashboard.md without adding
business logic. Supports MOCK_MODE for dashboard development before the live
pipeline is available, the response shape remains unchanged when switching to
live data.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from kuartal.api import mock_data
from kuartal.config import settings
from kuartal.pipeline import compute
from kuartal.pipeline.run import run_for_ticker
from kuartal.sectors import endpoints
from kuartal.sectors.client import SectorsAPIError, SectorsClient
from kuartal.storage.db import Database

logger = logging.getLogger("kuartal.api.server")
app = FastAPI(title="Kuartal API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate limiting -------------------------------------------------------
# Simple in-memory limiter per client IP and path.
# Multi-instance deployments need a shared store like Redis.
_RATE_LIMIT_WINDOW_SECONDS = 60
_RATE_LIMIT_MAX_REQUESTS = 60
_request_log: dict[str, deque] = defaultdict(deque)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{request.url.path}"
    now = time.monotonic()

    window = _request_log[key]
    while window and now - window[0] > _RATE_LIMIT_WINDOW_SECONDS:
        window.popleft()

    if len(window) >= _RATE_LIMIT_MAX_REQUESTS:
        return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})

    window.append(now)
    return await call_next(request)

def _get_db() -> Database:
    return Database()

def _build_live_card(db: Database, sectors_client: SectorsClient, watch) -> dict | None:
    """Build a CompanyCard from stored state and live trend/percentile data."""

    last_seen = db.get_last_seen(watch.ticker)
    if last_seen is None:
        return None

    verdict_entry = db.get_verdict(watch.ticker, last_seen.period) or db.latest_verdict(watch.ticker)
    if verdict_entry is None:
        return None

    try:
        financials     = endpoints.get_quarterly_financials(sectors_client, watch.ticker)
        own_trend      = compute.own_trend(financials)
        margins        = compute.margin_series(financials)
        this_growth    = compute.yoy_growth(financials)
        own_avg_growth = compute.own_avg_growth_4q(financials)
        peers          = endpoints.get_top_growth(sectors_client, watch.sector)
        peer_growths   = [p["growth"] for p in peers if p.get("ticker") != watch.ticker]
        percentile, peer_count = compute.sector_percentile(this_growth or 0.0, peer_growths)

    except SectorsAPIError as exc:
        logger.warning("could not refresh live fields for ticker=%s: %s", watch.ticker, exc)
        own_trend, margins, this_growth, own_avg_growth = [], [], 0.0, 0.0
        percentile, peer_count = verdict_entry.percentile, 0

    name = watch.ticker
    try:
        report = endpoints.get_company_report(sectors_client, watch.ticker)
        name = report.get("name") or name

    except SectorsAPIError:
        pass  # display-context-only call; fall back to ticker as the name

    return {
        "ticker":           watch.ticker,
        "name":             name,
        "sector":           watch.sector,
        "quarter":          verdict_entry.quarter,
        "status":           "new" if not verdict_entry.opened else "seen",
        "verdict":          verdict_entry.verdict,
        "direction":        verdict_entry.direction,
        "ownTrend":         own_trend,
        "ownAvgGrowth":     own_avg_growth or 0.0,
        "thisGrowth":       this_growth or 0.0,
        "sectorPercentile": percentile,
        "sectorPeerCount":  peer_count,
        "margin":           margins,
        "channel":          "Telegram",
        "lastSent":         verdict_entry.delivered_at.isoformat() if verdict_entry.delivered_at else "",
        "opened":           verdict_entry.opened,
        "timeToVerdict":    verdict_entry.time_to_verdict,
    }


@app.get("/api/watchlist")
def get_watchlist(scenario: str = "default"):
    """scenario="empty" represents the empty-watchlist state (mock mode only)."""

    if settings.mock_mode:
        return mock_data.mock_watchlist(cast(mock_data.Scenario, scenario))

    # --- live path -----------------------------------------------------
    db = _get_db()
    sectors_client = SectorsClient()
    companies = []
    for watch in db.list_watchlist():
        card = _build_live_card(db, sectors_client, watch)
        if card is not None:
            companies.append(card)

    recent = [
        {
            "ticker":  v.ticker,
            "verdict": v.verdict,
            "quarter": v.quarter,
            "sentAt":  v.delivered_at.isoformat() if v.delivered_at else ""
        }
        for v in db.recent_verdicts(limit=10)
    ]

    total           = len(db.list_watched_tickers())
    covered         = len(companies)
    coverage_rate   = round(covered / total, 2) if total else 0.0
    all_recent      = db.recent_verdicts(limit=100)
    opened_count    = sum(1 for v in all_recent if v.opened)
    engagement_rate = round(opened_count / len(all_recent), 2) if all_recent else 0.0

    metrics = {
        "timeToVerdictAvg": companies[0]["timeToVerdict"] if companies else "",
        "coverageRate": coverage_rate,
        "engagementRate": engagement_rate,
        # Not computed here - see backtest/analyze.py, which is the only
        # place this number is allowed to come from.
        "backtestCorrelation": 0.0,
    }

    return {"companies": companies, "recentVerdicts": recent, "metrics": metrics}


@app.get("/api/company/{ticker}")
def get_company(ticker: str):
    if settings.mock_mode:
        company = mock_data.mock_company(ticker.upper())
        if company is None:
            raise HTTPException(status_code=404, detail=f"No mock data for {ticker}")
        return company

    # --- live path -----------------------------------------------------
    db = _get_db()
    sectors_client = SectorsClient()
    watch = next((w for w in db.list_watchlist() if w.ticker == ticker.upper()), None)
    if watch is None:
        raise HTTPException(status_code=404, detail=f"{ticker} is not on the watchlist")

    card = _build_live_card(db, sectors_client, watch)
    if card is None:
        raise HTTPException(status_code=404, detail=f"No processed report yet for {ticker}")
    return card


@app.post("/api/dev/rerun/{ticker}")
def dev_rerun_pipeline(ticker: str):
    """Dev-only endpoint: re-runs pipeline/run.py against the last stored
    quarter for `ticker`, forcing a fresh verdict even if it matches
    last_seen_report. Backs the dashboard's "Simulate incoming report"
    button with a real run instead of frontend-only fakery.

    Not available in MOCK_MODE, and not meant for production traffic
    """

    if settings.mock_mode:
        raise HTTPException(status_code=400, detail="dev/rerun is only available with MOCK_MODE=false")

    db = _get_db()
    ticker = ticker.upper()
    watch = next((w for w in db.list_watchlist() if w.ticker == ticker), None)
    if watch is None:
        raise HTTPException(status_code=404, detail=f"{ticker} is not on the watchlist")

    sectors_client = SectorsClient()
    result = run_for_ticker(
        ticker=watch.ticker,
        sector=watch.sector,
        db=db,
        sectors_client=sectors_client,
        force=True
    )

    if result.status == "error":
        if result.error is None:
            raise HTTPException(status_code=502, detail="pipeline failed with an unknown error.")
        raise HTTPException(status_code=502, detail=f"pipeline failed at stage={result.error.stage}: {result.error.error}")

    return {"ticker": ticker, "status": result.status, "card": result.card}


@app.get("/api/pipeline-status/{ticker}")
def get_pipeline_status(ticker: str):
    """Provides data for the PipelineStrip component."""

    if settings.mock_mode:
        return mock_data.mock_pipeline_status(ticker.upper())
    raise HTTPException(status_code=501, detail="Live pipeline-status trace not wired yet - set MOCK_MODE=true")


@app.get("/api/health")
def health():
    return { "status": "ok", "mock_mode": settings.mock_mode }
