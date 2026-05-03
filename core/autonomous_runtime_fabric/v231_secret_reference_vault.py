from __future__ import annotations
from pathlib import Path
from .schemas import FabricArtifact, FabricStatus, new_id
from .storage import JsonStore

class SecretReferenceVault:
    """V231: secret reference vault, never stores raw secret."""
    def __init__(self, root: str | Path = ".autonomous_runtime_fabric_state"):
        self.store = JsonStore(Path(root) / "secret_references.json")
    def register_reference(self, name: str, provider: str = "env") -> FabricArtifact:
        ref = {"id": new_id("secret_ref"), "name": name, "provider": provider, "raw_value_stored": False}
        self.store.append(ref)
        return FabricArtifact(new_id("secretvault"), "secret_reference_vault", "security", FabricStatus.READY, 0.94, {"reference": ref, "total": len(self.store.read([]))})
