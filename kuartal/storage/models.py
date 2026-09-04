"""
Data models for the watchlist and last-seen reports.

These are the only persisted models in Kuartal. Keep them minimal to support
local SQLite storage for watched tickers and their latest delivered report dates.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Watchlist:
    ticker: str
    sector: str
    added_at: datetime

@dataclass
class LastSeenReport:
    ticker: str
    period: str # e.g. "Q2 2026"
    seen_at: datetime
