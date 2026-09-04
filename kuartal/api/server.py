"""
Thin API read layer over storage/db.py.

Exposes the dashboard endpoints defined in dashboard.md without adding
business logic. Supports MOCK_MODE for dashboard development before the live
pipeline is available, the response shape remains unchanged when switching to
live data.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from kuartal.api import mock_data
from kuartal.config import settings

app = FastAPI(title="Kuartal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/watchlist")
def get_watchlist(scenario: str = "default"):
    """scenario="empty" represents the empty-watchlist state."""

    if settings.mock_mode:
        return mock_data.mock_watchlist(scenario)

    # --- live path -----------------------------------------------------
    # TODO(backend owner): replace with live data from storage/db.py and
    # pipeline/run.py. Load the watchlist, attach the latest stored verdict or
    # a stale/seen card per ticker, and assemble recentVerdicts and metrics.
    # Return the exact WatchlistResponse schema defined in api/schemas.py.
    raise HTTPException(status_code=501, detail="Live pipeline not wired yet - set MOCK_MODE=true")


@app.get("/api/company/{ticker}")
def get_company(ticker: str):
    if settings.mock_mode:
        company = mock_data.mock_company(ticker.upper())
        if company is None:
            raise HTTPException(status_code=404, detail=f"No mock data for {ticker}")
        return company

    # --- live path -----------------------------------------------------
    raise HTTPException(status_code=501, detail="Live pipeline not wired yet - set MOCK_MODE=true")


@app.get("/api/pipeline-status/{ticker}")
def get_pipeline_status(ticker: str):
    """
    Provides data for the PipelineStrip component.

    Separate from the §3 dashboard contract and intended for polling during an
    active pipeline run.
    """

    if settings.mock_mode:
        return mock_data.mock_pipeline_status(ticker.upper())
    raise HTTPException(status_code=501, detail="Live pipeline not wired yet - set MOCK_MODE=true")


@app.get("/api/health")
def health():
    return { "status": "ok", "mock_mode": settings.mock_mode }
