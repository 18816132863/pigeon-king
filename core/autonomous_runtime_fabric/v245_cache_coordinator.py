from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class CacheCoordinator:
    """V245: cache coordination policy."""
    def plan(self, cache_items: int, stale_items: int) -> FabricArtifact:
        stale_ratio = stale_items / max(1, cache_items)
        action = "purge_stale" if stale_ratio > 0.2 else "keep"
        status = FabricStatus.WARN if stale_ratio > 0.2 else FabricStatus.READY
        return FabricArtifact(new_id("cache"), "cache_coordination", "cache", status, round(1 - stale_ratio, 4), {"cache_items": cache_items, "stale_items": stale_items, "action": action})
