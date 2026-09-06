"""
In-memory registry for tracking pipeline stages.

Used by `/api/pipeline-status/{ticker}` to show the current 4-step pipeline
status. pipeline/run.py updates each stage with mark(), while get()
returns the current status for a ticker.

This is process-local, so scheduler updates are not visible to the API
process. It works for runs triggered through the API, but a shared store
would be needed to support background scheduler runs.
"""

from __future__ import annotations

import threading

STEP_NAMES = ["report detected", "history read", "sector ranked", "verdict generated"]

_lock = threading.Lock()
_STATUS: dict[str, dict[str, str]] = {}

def reset(ticker: str) -> None:
    """Call at the start of a run: every step starts "pending"."""

    with _lock:
        _STATUS[ticker] = {name: "pending" for name in STEP_NAMES}

def mark(ticker: str, step_name: str, status: str) -> None:
    """status is one of "pending" | "in_progress" | "done" | "failed"."""

    with _lock:
        _STATUS.setdefault(ticker, {name: "pending" for name in STEP_NAMES})
        _STATUS[ticker][step_name] = status

def get(ticker: str) -> dict:
    """
    Returns the same shape as mock_pipeline_status, with all steps set to
    "pending" when no run is being tracked for the ticker.
    """

    with _lock:
        steps = _STATUS.get(ticker, {name: "pending" for name in STEP_NAMES})
        return {
            "ticker": ticker,
            "steps": [{
                "name": name, 
                "status": steps.get(name, "pending")
                } for name in STEP_NAMES],
        }
