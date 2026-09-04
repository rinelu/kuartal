"""
Structured prompts for LLM-generated descriptions.

Keeps the model instructions centralized and ensures the LLM is used only for
descriptive output, not investment advice, price targets, or buy/sell/hold
recommendations.
"""

from __future__ import annotations
from kuartal.pipeline.verdict import DISCLAIMER, VerdictPayload

SYSTEM_PROMPT = (
    "Write exactly one short, plain-language sentence describing the "
    "company's latest quarterly revenue growth in the context of its own "
    "recent trend and sector peers. Use only the facts and numbers provided. "
    "Be factual and neutral: do not make predictions, recommendations, "
    "judgments, or investment suggestions; do not mention buying, selling, "
    "holding, price targets, or valuation advice. Avoid advice-like wording "
    'such as "should", "consider", or "opportunity". Do not introduce any '
    "figures or claims that are not provided. "
    f'Always end with exactly this sentence: "{DISCLAIMER}"'
)

def build_user_prompt(payload: VerdictPayload) -> str:
    return (
        f"Ticker: {payload['ticker']}\n"
        f"Period: {payload['period']}\n"
        f"Revenue growth (YoY, this quarter): {payload['revenue_growth_yoy']:.0%}\n"
        f"Own average growth (trailing 4 quarters): {payload['own_avg_growth_4q']:.0%}\n"
        f"Sector: {payload['sector']}\n"
        f"Sector percentile (this quarter): {payload['sector_percentile']}\n\n"
        "Write the one-sentence descriptive verdict now."
    )
