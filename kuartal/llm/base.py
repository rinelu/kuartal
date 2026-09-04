"""
Provider-agnostic interface for LLM integrations.

Defines the common interface used by Kuartal so LLM providers can be swapped
without coupling the pipeline to a specific implementation.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from kuartal.pipeline.verdict import VerdictPayload

class LLMProvider(ABC):
    @abstractmethod
    def generate_verdict(self, payload: VerdictPayload) -> str:
        """
        Generate a short, plain-language, descriptive verdict from the structured
        payload defined in pipeline/verdict.py.

        The output must remain descriptive and must not contain buy, sell, or hold
        language. This constraint is enforced by the prompt template, but callers
        should also treat the result as descriptive-only.
        """
