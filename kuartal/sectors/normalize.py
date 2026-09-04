"""
Helpers for ticker normalization and response shaping.

Normalizes ticker formats and response structures across Sectors endpoints,
so the rest of the pipeline can work with consistent data.
"""

from __future__ import annotations

def normalize_ticker(raw: str) -> str:
    """Return the canonical ticker format: uppercase with no exchange suffix.

    >>> normalize_ticker("bbri.jk")
    'BBRI'
    """
    return raw.strip().upper().split(".")[0]
