from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, GateDecision, new_id

class UserAcceptanceGate:
    """V217: user acceptance gate."""
    def evaluate(self, signals: list[str]) -> ControlArtifact:
        ok = any(s in signals for s in ["PASS", "通过", "欧克", "ok"])
        needs_change = any(s in signals for s in ["不行", "失败", "报错"])
        decision = GateDecision.FAIL if needs_change else (GateDecision.PASS if ok else GateDecision.WARN)
        status = PlaneStatus.BLOCKED if decision == GateDecision.FAIL else (PlaneStatus.READY if decision == GateDecision.PASS else PlaneStatus.WARN)
        return ControlArtifact(new_id("uat"), "user_acceptance_gate", "uat", status, 0.9 if ok else 0.7, {"signals": signals, "decision": decision.value})
