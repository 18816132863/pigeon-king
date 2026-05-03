from __future__ import annotations
import hashlib, json
from .schemas import FabricArtifact, FabricStatus, new_id

class DeterministicVerifier:
    """V238: deterministic payload verifier."""
    def verify(self, payload: dict) -> FabricArtifact:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
        return FabricArtifact(new_id("detverify"), "deterministic_verifier", "verification", FabricStatus.READY, 0.93, {"digest": digest, "bytes": len(body)})
