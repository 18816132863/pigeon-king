from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class DegradationController:
    """V240: graceful degradation controller."""
    def choose_mode(self, unavailable: list[str]) -> FabricArtifact:
        if not unavailable:
            mode, score, status = "full", 0.95, FabricStatus.READY
        elif "model" in unavailable:
            mode, score, status = "rule_based_fallback", 0.62, FabricStatus.DEGRADED
        else:
            mode, score, status = "partial", 0.78, FabricStatus.WARN
        return FabricArtifact(new_id("degrade"), "degradation_mode", "degradation", status, score, {"unavailable": unavailable, "mode": mode})
