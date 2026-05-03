from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, GateDecision, new_id

class CanaryDeploymentController:
    """V205: canary deployment controller."""
    def evaluate(self, canary_score: float, error_rate: float) -> ControlArtifact:
        if canary_score >= 0.9 and error_rate <= 0.03:
            decision = GateDecision.PASS
            status = PlaneStatus.READY
        elif canary_score >= 0.75 and error_rate <= 0.1:
            decision = GateDecision.WARN
            status = PlaneStatus.WARN
        else:
            decision = GateDecision.FAIL
            status = PlaneStatus.BLOCKED
        return ControlArtifact(new_id("canary"), "canary_deployment", "canary", status, canary_score, {"error_rate": error_rate, "decision": decision.value})
