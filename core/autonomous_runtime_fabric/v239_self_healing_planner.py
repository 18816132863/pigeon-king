from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class SelfHealingPlanner:
    """V239: self-healing planner."""
    def plan(self, symptoms: list[str]) -> FabricArtifact:
        steps = []
        if "provider_down" in symptoms:
            steps.append("switch_provider")
        if "quota_near_limit" in symptoms:
            steps.append("throttle_and_batch")
        if "verification_failed" in symptoms:
            steps.append("rollback_to_snapshot")
        if not steps:
            steps.append("monitor")
        status = FabricStatus.WARN if symptoms else FabricStatus.READY
        return FabricArtifact(new_id("heal"), "self_healing_plan", "healing", status, 0.86, {"symptoms": symptoms, "steps": steps})
