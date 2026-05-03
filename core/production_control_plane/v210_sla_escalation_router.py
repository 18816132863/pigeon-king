from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, Severity, new_id

class SLAEscalationRouter:
    """V210: SLA escalation router."""
    def route(self, delay_minutes: int, severity: Severity) -> ControlArtifact:
        if severity in {Severity.HIGH, Severity.CRITICAL} or delay_minutes > 60:
            target = "owner_immediate"
            status = PlaneStatus.WARN
        elif delay_minutes > 15:
            target = "operator_queue"
            status = PlaneStatus.READY
        else:
            target = "normal_log"
            status = PlaneStatus.READY
        return ControlArtifact(new_id("sla"), "sla_escalation", "sla", status, 0.86, {"delay_minutes": delay_minutes, "severity": severity.value, "target": target})
