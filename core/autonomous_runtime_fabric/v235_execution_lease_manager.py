from __future__ import annotations
from pathlib import Path
from .schemas import FabricArtifact, FabricStatus, new_id, now_ts
from .storage import JsonStore

class ExecutionLeaseManager:
    """V235: execution lease manager."""
    def __init__(self, root: str | Path = ".autonomous_runtime_fabric_state"):
        self.store = JsonStore(Path(root) / "execution_leases.json")
    def acquire(self, owner: str, resource: str, ttl_seconds: int = 600) -> FabricArtifact:
        lease = {"id": new_id("lease"), "owner": owner, "resource": resource, "expires_at": now_ts() + ttl_seconds}
        self.store.append(lease)
        return FabricArtifact(new_id("lease_artifact"), "execution_lease", "lease", FabricStatus.READY, 0.9, {"lease": lease})
