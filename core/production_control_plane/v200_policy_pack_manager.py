from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class PolicyPackManager:
    """V200: composable policy pack manager."""
    def compile(self, mode: str = "strict") -> ControlArtifact:
        packs = {
            "safety": ["no_secret_exfiltration", "high_risk_approval", "dry_run_default"],
            "release": ["verify_before_promote", "snapshot_before_release", "rollback_plan_required"],
            "personal": ["one_shot_package", "direct_command", "avoid_incremental_patch"],
        }
        if mode == "strict":
            packs["strict"] = ["block_unknown_install", "block_unapproved_external_send"]
        return ControlArtifact(new_id("policy_pack"), "policy_pack", "policy", PlaneStatus.READY, 0.94, {"mode": mode, "packs": packs})
