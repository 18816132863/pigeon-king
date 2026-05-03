from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class ConnectorPermissionReviewer:
    """V189: connector permission reviewer."""
    def review(self, connectors: list[dict]) -> IntelligenceArtifact:
        risky = []
        for c in connectors:
            perms = set(c.get("permissions", []))
            if perms & {"external_send", "payment", "install", "secret_access", "delete"}:
                risky.append(c.get("name", "unknown"))
        score = 1 - len(risky) / max(1, len(connectors))
        status = IntelligenceStatus.READY if score >= 0.75 else IntelligenceStatus.WARN
        return IntelligenceArtifact(new_id("permreview"), "connector_permission_review", "permission", status, round(score, 4), {"risky_connectors": risky})
