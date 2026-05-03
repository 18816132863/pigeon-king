from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class TrustZoneManager:
    """V242: trust zone manager."""
    def classify(self, resource: str) -> FabricArtifact:
        if any(x in resource.lower() for x in ["secret", "token", "payment"]):
            zone = "restricted"
            score = 0.8
        elif any(x in resource.lower() for x in ["external", "email", "customer"]):
            zone = "controlled"
            score = 0.86
        else:
            zone = "standard"
            score = 0.94
        return FabricArtifact(new_id("trust"), "trust_zone", "trust", FabricStatus.READY, score, {"resource": resource, "zone": zone})
