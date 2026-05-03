from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class RunbookExecutor:
    """V219: safe dry-run runbook executor."""
    def dry_run(self, playbook_artifact) -> ControlArtifact:
        steps = playbook_artifact.payload.get("steps", [])
        executed = [{"step": s, "mode": "dry_run", "side_effect": False} for s in steps]
        return ControlArtifact(new_id("runbook"), "runbook_dry_run", "runbook", PlaneStatus.READY, 0.92, {"executed": executed})
