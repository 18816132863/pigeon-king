from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class MemoryTierManager:
    """V249: memory tier manager."""
    def tier(self, memories: list[dict]) -> FabricArtifact:
        tiers = {"hot": [], "warm": [], "cold": []}
        for m in memories:
            importance = float(m.get("importance", 0.5))
            key = "hot" if importance >= 0.8 else ("warm" if importance >= 0.45 else "cold")
            tiers[key].append(m.get("id", "unknown"))
        return FabricArtifact(new_id("memorytier"), "memory_tiers", "memory", FabricStatus.READY, 0.9, {"tiers": tiers})
