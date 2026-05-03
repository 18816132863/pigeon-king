from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class CostAnalyzer:
    """V178: cost analysis and cost guard suggestions."""
    def analyze(self, token_estimate: int, model_group: str = "balanced") -> IntelligenceArtifact:
        unit = 0.000002 if model_group == "fast_low_cost" else 0.00001
        est_cost = round(token_estimate * unit, 4)
        recommendation = "downgrade_or_batch" if est_cost > 1.0 else "within_budget"
        score = 0.95 if recommendation == "within_budget" else 0.72
        status = IntelligenceStatus.READY if score >= 0.8 else IntelligenceStatus.WARN
        return IntelligenceArtifact(new_id("cost"), "cost_analysis", "cost", status, score, {"token_estimate": token_estimate, "estimated_cost": est_cost, "recommendation": recommendation})
