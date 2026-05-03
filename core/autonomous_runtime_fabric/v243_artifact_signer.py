from __future__ import annotations
import hashlib
from .schemas import FabricArtifact, FabricStatus, new_id

class ArtifactSigner:
    """V243: artifact signing manifest using deterministic digest."""
    def sign(self, file_names: list[str]) -> FabricArtifact:
        body = "\n".join(sorted(file_names))
        signature = hashlib.sha256(body.encode("utf-8")).hexdigest()[:24]
        return FabricArtifact(new_id("sign"), "artifact_signature", "signature", FabricStatus.READY, 0.94, {"files": sorted(file_names), "signature": signature})
