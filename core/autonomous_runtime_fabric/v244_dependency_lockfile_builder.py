from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class DependencyLockfileBuilder:
    """V244: dependency lockfile builder."""
    def build(self, deps: dict[str, str]) -> FabricArtifact:
        locked = {k: v for k, v in sorted(deps.items())}
        floating = [k for k, v in locked.items() if v in {"*", "latest", ""}]
        status = FabricStatus.WARN if floating else FabricStatus.READY
        score = 1 - len(floating) / max(1, len(locked))
        return FabricArtifact(new_id("lock"), "dependency_lockfile", "dependency", status, round(score, 4), {"locked": locked, "floating": floating})
