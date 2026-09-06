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
    user: str = "default"

@dataclass
class LastSeenReport:
    ticker: str
    period: str # e.g. "Q2 2026"
    seen_at: datetime

@dataclass
class VerdictLogEntry:
    ticker: str
    quarter: str
    verdict: str
    direction: str # "above" | "below" | "inline"
    percentile: int
    delivered_at: datetime | None
    opened: bool = False
    time_to_verdict: str = "" # e.g. "3m 40s", feeds the dashboard metric
    delivery_status: str = "not_attempted"  # "not_attempted" | "sent" | "failed"

@dataclass
class UserChatId:
    user: str
    chat_id: str
