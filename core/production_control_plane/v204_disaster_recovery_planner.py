from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, Severity, new_id

class DisasterRecoveryPlanner:
    """V204: disaster recovery planner."""
    def plan(self, severity: Severity = Severity.MEDIUM) -> ControlArtifact:
        steps = ["freeze writes", "capture evidence", "restore snapshot", "rerun verification", "write postmortem"]
        if severity in {Severity.HIGH, Severity.CRITICAL}:
            steps.insert(1, "disable external side effects")
            steps.append("manual approval before resume")
        return ControlArtifact(new_id("dr"), "disaster_recovery_plan", "recovery", PlaneStatus.READY, 0.88, {"severity": severity.value, "steps": steps})
