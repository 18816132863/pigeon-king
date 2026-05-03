from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, GateDecision, new_id

class GovernanceBoard:
    """V223: governance board decision builder."""
    def decide(self, readiness: float, risk_open: bool) -> ControlArtifact:
        if readiness >= 0.85 and not risk_open:
            decision, status = GateDecision.PASS, PlaneStatus.READY
        elif readiness >= 0.7:
            decision, status = GateDecision.WARN, PlaneStatus.WARN
        else:
            decision, status = GateDecision.FAIL, PlaneStatus.BLOCKED
        return ControlArtifact(new_id("gov"), "governance_board", "governance", status, readiness, {"decision": decision.value, "risk_open": risk_open})
