from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class ControlTower:
    """V227: central control tower summary."""
    def build(self, layers: list[str]) -> FabricArtifact:
        payload = {"layers": layers, "active_layers": len(layers), "mode": "autonomous_runtime_fabric"}
        score = 0.95 if len(layers) >= 8 else 0.7
        status = FabricStatus.READY if score >= 0.8 else FabricStatus.WARN
        return FabricArtifact(new_id("tower"), "control_tower", "control", status, score, payload)
