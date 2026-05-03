from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class CapacityPlanner:
    """V212: capacity planner."""
    def plan(self, expected_tasks: int, current_capacity: int) -> ControlArtifact:
        ratio = expected_tasks / max(1, current_capacity)
        if ratio <= 0.7:
            status, score, action = PlaneStatus.READY, 0.92, "capacity_ok"
        elif ratio <= 1.0:
            status, score, action = PlaneStatus.WARN, 0.75, "prepare_scale_up"
        else:
            status, score, action = PlaneStatus.WARN, 0.62, "scale_required"
        return ControlArtifact(new_id("capacity"), "capacity_plan", "capacity", status, score, {"expected_tasks": expected_tasks, "current_capacity": current_capacity, "action": action})
