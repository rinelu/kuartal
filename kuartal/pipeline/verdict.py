"""
Builds the structured payload used by the LLM for narration.

Keeps the LLM input limited to pre-computed values rather than raw financial
data, ensuring the generated output stays concise and grounded in the
pipeline's calculations.
"""

from __future__ import annotations
from typing import TypedDict

DISCLAIMER = "DISCLAIMER :: This is descriptive information, not investment advice."

class VerdictPayload(TypedDict):
    ticker:             str
    period:             str
    revenue_growth_yoy: float
    own_avg_growth_4q:  float
    sector:             str
    sector_percentile:  int

def build_verdict_payload(
    ticker:             str,
    period:             str,
    revenue_growth_yoy: float,
    own_avg_growth_4q:  float,
    sector:             str,
    sector_percentile:  int,
) -> VerdictPayload:
    return {
        "ticker":             ticker,
        "period":             period,
        "revenue_growth_yoy": revenue_growth_yoy,
        "own_avg_growth_4q":  own_avg_growth_4q,
        "sector":             sector,
        "sector_percentile":  sector_percentile,
    }
