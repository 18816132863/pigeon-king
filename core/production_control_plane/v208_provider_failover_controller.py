from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class ProviderFailoverController:
    """V208: provider failover policy."""
    def choose(self, providers: list[dict]) -> ControlArtifact:
        ranked = sorted(providers, key=lambda p: (p.get("healthy", False), -p.get("latency", 9999), p.get("quality", 0)), reverse=True)
        primary = ranked[0] if ranked else {"name": "none", "healthy": False}
        status = PlaneStatus.READY if primary.get("healthy") else PlaneStatus.WARN
        return ControlArtifact(new_id("failover"), "provider_failover", "provider", status, 0.88 if primary.get("healthy") else 0.55, {"primary": primary, "ranked": ranked})
