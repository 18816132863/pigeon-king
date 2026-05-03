from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class RuntimeMeshRegistry:
    """V228: runtime mesh node registry."""
    def register(self, nodes: list[dict]) -> FabricArtifact:
        healthy = [n for n in nodes if n.get("healthy", True)]
        score = len(healthy) / max(1, len(nodes))
        status = FabricStatus.READY if score >= 0.8 else FabricStatus.DEGRADED
        return FabricArtifact(new_id("mesh"), "runtime_mesh_registry", "mesh", status, score, {"nodes": nodes, "healthy": len(healthy)})
