"""
Fixture data for MOCK_MODE, allowing the dashboard to be developed against
realistic data before the live pipeline is available.
"""

from __future__ import annotations
from typing import Literal

_BBRI = {
    "ticker":  "BBRI",
    "name":    "Bank Rakyat Indonesia",
    "sector":  "Banks",
    "quarter": "Q2 2026",
    "status":  "new",
    "verdict": (
        "BBRI's revenue grew 9% this quarter - below its own 15% average "
        "over the last four quarters, and around the 65th percentile of "
        "the banking sector this period. This is descriptive information, "
        "not investment advice."
    ),
    "direction": "below",
    "ownTrend": [
        {"q": "Q1'25", "revenue": 62, "earnings": 24},
        {"q": "Q2'25", "revenue": 64, "earnings": 25},
        {"q": "Q3'25", "revenue": 66, "earnings": 25},
        {"q": "Q4'25", "revenue": 69, "earnings": 27},
        {"q": "Q1'26", "revenue": 70, "earnings": 27},
        {"q": "Q2'26", "revenue": 72, "earnings": 28},
    ],
    "ownAvgGrowth":     0.15,
    "thisGrowth":       0.09,
    "sectorPercentile": 65,
    "sectorPeerCount":  34,
    "margin":           [39.5, 39.1, 40.3, 40.9, 41.1, 40.8],
    "channel":          "Telegram",
    "lastSent":         "2026-09-04T03:12:00Z",
    "opened":           True,
    "timeToVerdict":    "3m 40s",
}

_BBTN = {
    "ticker":  "BBTN",
    "name":    "Bank Tabungan Negara",
    "sector":  "Banks",
    "quarter": "Q1 2026",
    "status":  "seen",  # stale: no new report this cycle,
                        # dashboard should grey the status and hide the "new" badge
    "verdict": (
        "BBTN's revenue grew 4% last quarter - in line with its own 5% "
        "average over the prior four quarters, and around the 40th "
        "percentile of the banking sector that period. This is descriptive "
        "information, not investment advice."
    ),
    "direction": "inline",
    "ownTrend": [
        {"q": "Q4'24", "revenue": 18, "earnings": 5},
        {"q": "Q1'25", "revenue": 18, "earnings": 5},
        {"q": "Q2'25", "revenue": 19, "earnings": 5},
        {"q": "Q3'25", "revenue": 19, "earnings": 6},
        {"q": "Q4'25", "revenue": 20, "earnings": 6},
        {"q": "Q1'26", "revenue": 20, "earnings": 6},
    ],
    "ownAvgGrowth":     0.05,
    "thisGrowth":       0.04,
    "sectorPercentile": 40,
    "sectorPeerCount":  34,
    "margin":           [27.1, 27.4, 27.0, 27.6, 27.8, 27.5],
    "channel":          "Telegram",
    "lastSent":         "2026-06-01T02:05:00Z",
    "opened":           True,
    "timeToVerdict":    "4m 12s",
}

_RECENT_VERDICTS = [
    {"ticker": "BBRI", "verdict": "Revenue grew 9%, below its own 4Q average.", "quarter": "Q2 2026", "sentAt": "2026-09-04T03:12:00Z"},
    {"ticker": "TLKM", "verdict": "Revenue grew 12%, above its own 4Q average.", "quarter": "Q2 2026", "sentAt": "2026-09-03T22:40:00Z"},
    {"ticker": "BBTN", "verdict": "Revenue grew 4%, in line with its own 4Q average.", "quarter": "Q1 2026", "sentAt": "2026-06-01T02:05:00Z"},
]

_METRICS = {
    "timeToVerdictAvg":    "3m 58s",
    "coverageRate":        0.92,
    "engagementRate":      0.71,
    "backtestCorrelation": 0.64,
}

Scenario = Literal["default", "empty"]

def mock_watchlist(scenario: Scenario = "default") -> dict:
    if scenario == "empty":
        return {"companies": [], "recentVerdicts": [], "metrics": _METRICS}
    return {
        "companies":      [_BBRI, _BBTN],
        "recentVerdicts": _RECENT_VERDICTS,
        "metrics":        _METRICS,
    }

def mock_company(ticker: str) -> dict | None:
    for company in (_BBRI, _BBTN):
        if company["ticker"] == ticker:
            return company
    return None


def mock_pipeline_status(ticker: str) -> dict:
    """
    Stub data for PipelineStrip's four-step live trace.
    Intended as a lightweight polling target.
    """

    return {
        "ticker": ticker,
        "steps": [
            {"name": "report detected",   "status": "done"},
            {"name": "history read",      "status": "done"},
            {"name": "sector ranked",     "status": "in_progress"},
            {"name": "verdict generated", "status": "pending"},
        ],
    }
