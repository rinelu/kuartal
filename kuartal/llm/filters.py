"""
Checks LLM verdicts before they are delivered.

These checks are a hard gate: anything that fails must not be delivered
as-is. `llm/service.py` retries once, then falls back to a deterministic
sentence built only from the computed values.
"""

from __future__ import annotations
import re

# Case-insensitive word-boundary match.
# Keep this broad: false positives are safer than letting 
# advice-like language through.
ADVICE_TERMS = [
    r"\bbuy\b", r"\bbuys\b", r"\bbuying\b",
    r"\bsell\b", r"\bsells\b", r"\bselling\b",
    r"\bhold\b", r"\bholds\b", r"\bholding\b",
    r"\baccumulate\b", r"\baccumulating\b",
    r"\boverweight\b", r"\bunderweight\b",
    r"\boutperform\b", r"\bunderperform\b",
    r"\btarget price\b", r"\bprice target\b",
    r"\bshould invest\b", r"\bshould buy\b", r"\bshould sell\b",
    r"\brecommend(ed|s|ation)?\b",
    r"\bgood (time|entry|opportunity)\b",
    r"\bworth (buying|selling)\b",
]

_ADVICE_PATTERN = re.compile("|".join(ADVICE_TERMS), re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

def contains_advice_language(text: str) -> bool:
    return bool(_ADVICE_PATTERN.search(text))

def sentence_count(text: str) -> int:
    stripped = text.strip()
    if not stripped: return 0

    return len([s for s in _SENTENCE_SPLIT.split(stripped) if s.strip()])

def within_length(text: str, min_sentences: int = 1, max_sentences: int = 3) -> bool:
    """
    Keep verdicts within the 2–3 sentence plain-language format.

    `min_sentences` defaults to 1 to allow a single valid sentence;
    `max_sentences` is the hard limit.
    """

    count = sentence_count(text)
    return min_sentences <= count <= max_sentences

def passes_all_checks(text: str) -> bool:
    return within_length(text) and not contains_advice_language(text)
