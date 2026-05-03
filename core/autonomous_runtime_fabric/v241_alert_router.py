from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, FabricSeverity, new_id

class AlertRouter:
    """V241: alert router."""
    def route(self, severity: FabricSeverity) -> FabricArtifact:
        target = {
            FabricSeverity.LOW: "log_only",
            FabricSeverity.MEDIUM: "operator_inbox",
            FabricSeverity.HIGH: "owner_notification",
            FabricSeverity.CRITICAL: "freeze_and_owner_notification",
        }[severity]
        status = FabricStatus.WARN if severity in {FabricSeverity.HIGH, FabricSeverity.CRITICAL} else FabricStatus.READY
        return FabricArtifact(new_id("alert"), "alert_route", "alert", status, 0.88, {"severity": severity.value, "target": target})
