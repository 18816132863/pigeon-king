from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class ConfigOverlayManager:
    """V230: environment/profile config overlay manager."""
    def merge(self, base_config: dict, overlay: dict) -> FabricArtifact:
        merged = dict(base_config)
        merged.update(overlay)
        conflicts = [k for k in overlay if k in base_config and base_config[k] != overlay[k]]
        status = FabricStatus.WARN if conflicts else FabricStatus.READY
        score = 0.82 if conflicts else 0.93
        return FabricArtifact(new_id("config"), "config_overlay", "config", status, score, {"merged": merged, "conflicts": conflicts})
