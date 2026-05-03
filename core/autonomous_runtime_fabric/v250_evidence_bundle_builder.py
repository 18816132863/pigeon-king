from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class EvidenceBundleBuilder:
    """V250: evidence bundle builder."""
    def build(self, records: list[dict]) -> FabricArtifact:
        redacted = []
        for r in records:
            text = str(r.get("text", ""))
            if any(x in text.lower() for x in ["token", "secret", "api_key"]):
                text = "[REDACTED]"
            redacted.append({"id": r.get("id", new_id("record")), "text": text})
        return FabricArtifact(new_id("evidence"), "evidence_bundle", "evidence", FabricStatus.READY, 0.93, {"records": redacted, "count": len(redacted)})
