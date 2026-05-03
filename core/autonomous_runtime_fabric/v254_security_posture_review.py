from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, FabricSeverity, new_id

class SecurityPostureReview:
    """V254: security posture review."""
    def review(self, findings: list[str]) -> FabricArtifact:
        critical_words = ["secret_leak", "unapproved_payment", "raw_token"]
        critical = [f for f in findings if f in critical_words]
        high = [f for f in findings if "unapproved" in f and f not in critical]
        if critical:
            status, severity, score = FabricStatus.BLOCKED, FabricSeverity.CRITICAL, 0.25
        elif high:
            status, severity, score = FabricStatus.WARN, FabricSeverity.HIGH, 0.7
        else:
            status, severity, score = FabricStatus.READY, FabricSeverity.LOW, 0.94
        return FabricArtifact(new_id("secposture"), "security_posture", "security", status, score, {"severity": severity.value, "findings": findings})
