"""
Helpers for ticker normalization and response shaping.

Normalizes ticker formats and response structures across Sectors endpoints,
so the rest of the pipeline can work with consistent data.
"""

from __future__ import annotations
from typing import Any

def normalize_ticker(raw: str) -> str:
    """Return the canonical ticker format: uppercase with no exchange suffix.

    >>> normalize_ticker("bbri.jk")
    'BBRI'
    """
    return raw.strip().upper().split(".")[0]

def _to_float(value: Any) -> float | None:
    """
    Convert a numeric field to float when possible.

    The Sectors API may return numbers as JSON values or strings, so this
    keeps that inconsistency out of the rest of the pipeline.
    """

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip().replace(",", "")
        if not stripped:   return None
        try:               return float(stripped)
        except ValueError: return None

    return None


def normalize_quarter_label(raw: str) -> str:
    """
    Return quarter labels in the pipeline's Q<n>'<yy> format.

    Accepts common formats like 2025Q1, 2025-Q1, and Q1 2025, while
    leaving already-canonical values unchanged.

    >>> normalize_quarter_label("2025Q1")
    "Q1'25"
    >>> normalize_quarter_label("Q1 2025")
    "Q1'25"
    >>> normalize_quarter_label("Q1'25")
    "Q1'25"
    """

    raw = raw.strip()
    if "'" in raw and raw[0].upper() == "Q":
        return raw

    import re

    match = re.search(r"(?P<q>[1-4])", raw)
    year_match = re.search(r"(?P<year>\d{4})", raw)
    if match and year_match:
        quarter = match.group("q")
        year = year_match.group("year")[-2:]
        return f"Q{quarter}'{year}"

    return raw

def normalize_financial_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize one quarterly financials entry to the pipeline's expected shape.

    Maps upstream field names to q, revenue, earnings, and margin,
    and converts numeric values to floats.
    """

    quarter = entry.get("q") or entry.get("quarter") or entry.get("period") or ""
    revenue = entry.get("revenue")
    if revenue is None:
        revenue = entry.get("total_revenue")

    earnings = entry.get("earnings")
    if earnings is None:
        earnings = entry.get("net_income")

    margin = entry.get("margin")
    if margin is None:
        margin = entry.get("net_margin")

    return {
        "q": normalize_quarter_label(str(quarter)) if quarter else "",
        "revenue": _to_float(revenue) or 0.0,
        "earnings": _to_float(earnings) or 0.0,
        "margin": _to_float(margin),
    }

def normalize_financials(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a list of quarterly-financials entries, oldest-first."""

    return [normalize_financial_entry(e) for e in entries]

def normalize_growth_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a single top-growth ranking entry.

    Ensures `ticker` is canonical and `growth` is a float, so
    `pipeline/compute.sector_percentile` can consume the list directly.
    """

    ticker = entry.get("ticker") or entry.get("symbol") or ""
    growth = entry.get("growth")
    if growth is None:
        growth = entry.get("revenue_growth")

    return {
        "ticker": normalize_ticker(str(ticker)) if ticker else "",
        "growth": _to_float(growth),
    }


def normalize_growth_rankings(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a list of top-growth ranking entries."""

    return [normalize_growth_entry(e) for e in entries]
