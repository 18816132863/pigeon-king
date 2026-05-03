from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class ModelCanaryEvaluator:
    """V207: model canary evaluator."""
    def compare(self, baseline: float, candidate: float, max_regression: float = 0.03) -> ControlArtifact:
        delta = candidate - baseline
        passed = delta >= -max_regression
        status = PlaneStatus.READY if passed else PlaneStatus.WARN
        score = max(0.0, min(1.0, 0.85 + delta))
        return ControlArtifact(new_id("model_canary"), "model_canary", "model", status, score, {"baseline": baseline, "candidate": candidate, "delta": round(delta, 4), "passed": passed})
