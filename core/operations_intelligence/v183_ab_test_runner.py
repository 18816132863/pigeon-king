from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class ABTestRunner:
    """V183: deterministic A/B test runner."""
    def run(self, variant_a: dict, variant_b: dict) -> IntelligenceArtifact:
        score_a = float(variant_a.get("quality", 0.7)) - float(variant_a.get("cost", 0.1)) * 0.1
        score_b = float(variant_b.get("quality", 0.7)) - float(variant_b.get("cost", 0.1)) * 0.1
        winner = "A" if score_a >= score_b else "B"
        return IntelligenceArtifact(new_id("ab"), "ab_test_result", "ab_test", IntelligenceStatus.READY, max(score_a, score_b), {"score_a": round(score_a, 4), "score_b": round(score_b, 4), "winner": winner})
