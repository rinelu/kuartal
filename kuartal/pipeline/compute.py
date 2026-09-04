"""
Computes own-trend changes and sector-relative metrics.

All calculations are deterministic and operate on plain data, with no LLM
involvement.
"""

from __future__ import annotations
from typing import TypedDict

class QuarterFinancial(TypedDict):
    q:        str# e.g. "Q1'25"
    revenue:  float
    earnings: float
    margin:   float | None

def own_trend(financials: list[QuarterFinancial], n_quarters: int = 6) -> list[dict]:
    """Return the last `n_quarters` of quarterly data: `quarter`, `revenue`, and `earnings`."""

    trimmed = financials[-n_quarters:]
    return [ { "q": f["q"], "revenue": f["revenue"], "earnings": f["earnings"] } for f in trimmed ]

def margin_series(financials: list[QuarterFinancial], n_quarters: int = 6) -> list[float]:
    """Return the last `n_quarters` of margin data."""

    trimmed = financials[-n_quarters:]
    return [ margin for f in trimmed if (margin := f.get("margin")) is not None ]

def yoy_growth(financials: list[QuarterFinancial], metric: str = "revenue") -> float | None:
    """
    Return the year-over-year growth for the latest quarter.

    Compares the latest quarter with the same quarter one year earlier.
    Returns `None` when fewer than five quarters of history are available.
    """

    if len(financials) < 5: return None

    current  = financials[-1][metric]
    year_ago = financials[-5][metric]
    if year_ago == 0: return None

    return round((current - year_ago) / year_ago, 4)

def own_avg_growth_4q(financials: list[QuarterFinancial], metric: str = "revenue") -> float | None:
    """Average year-over-year growth over the trailing four quarters."""

    growths = []
    for i in range(len(financials) - 4, len(financials)):
        if i - 4 < 0: continue

        prev = financials[i - 4][metric]
        cur  = financials[i][metric]
        if prev == 0: continue

        growths.append((cur - prev) / prev)

    if not growths: return None

    return round(sum(growths) / len(growths), 4)

def sector_percentile(ticker_growth: float, peer_growths: list[float]) -> tuple[int, int]:
    """
    Calculate ticker_growth's percentile rank among peer_growths on a 0–100
    scale, along with the number of peers. Maps to sectorPercentile and
    sectorPeerCount.
    """

    peers = [g for g in peer_growths if g is not None]
    if not peers: return 50, 0

    below_or_equal = sum(1 for g in peers if g <= ticker_growth)
    percentile     = round(100 * below_or_equal / len(peers))
    return percentile, len(peers)


def direction(this_growth: float, own_avg_growth: float | None, tolerance: float = 0.02) -> str:
    """
    Classify the current value as "above", "below", or "inline" relative to
    the company's trailing average. 

    `tolerance` defines the range considered "inline" and maps to direction.
    """

    if own_avg_growth is None: return "inline"

    delta = this_growth - own_avg_growth
    if delta > tolerance:  return "above"
    if delta < -tolerance: return "below"
    return "inline"
