from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class AuditExporter:
    """V193: audit export builder."""
    def export(self, events: list[dict]) -> IntelligenceArtifact:
        redacted_events = []
        for e in events:
            msg = str(e.get("message", ""))
            if any(x in msg.lower() for x in ["token", "secret", "api_key", "密码", "密钥"]):
                msg = "[REDACTED_SENSITIVE_EVENT]"
            redacted_events.append({"type": e.get("type", "event"), "message": msg})
        return IntelligenceArtifact(new_id("audit"), "audit_export", "audit", IntelligenceStatus.READY, 0.92, {"events": redacted_events, "count": len(redacted_events)})
