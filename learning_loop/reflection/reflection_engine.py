from __future__ import annotations

from .failure_pattern_analyzer import FailurePatternAnalyzer
from .success_pattern_promoter import SuccessPatternPromoter


class ReflectionEngine:
    """Turn outcomes into concrete next-run improvements."""

    def __init__(self) -> None:
        self.failures = FailurePatternAnalyzer()
        self.successes = SuccessPatternPromoter()

    def reflect(self, events: list[dict]) -> dict:
        return {
            "status": "reflected",
            "failure_analysis": self.failures.analyze(events),
            "success_promotion": self.successes.promote(events),
            "next_run_policy": "reuse_success_and_precheck_failures",
        }
