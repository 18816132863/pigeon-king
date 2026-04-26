from __future__ import annotations


class DelegationPlanner:
    """Break a mission into role-owned subtasks."""

    def delegate(self, mission: dict, roles: dict) -> dict:
        objective = mission.get("objective") or mission.get("goal") or "unknown"
        tasks = []
        for role in ["strategist", "critic", "operator", "verifier", "learner"]:
            tasks.append({
                "role": role,
                "task": f"{role}_work_for_{objective}",
                "side_effect": False,
                "requires_confirmation": False,
                "capabilities": roles.get(role, {}).get("capabilities", []),
            })
        return {"status": "delegated", "objective": objective, "tasks": tasks}
