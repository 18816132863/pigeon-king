from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class ReplayLab:
    """V237: replay lab for run simulation."""
    def replay(self, events: list[dict]) -> FabricArtifact:
        failures = [e for e in events if e.get("status") == "failed"]
        score = 1 - len(failures) / max(1, len(events))
        status = FabricStatus.READY if not failures else FabricStatus.WARN
        return FabricArtifact(new_id("replay"), "replay_lab", "replay", status, round(score, 4), {"events": len(events), "failures": failures})
