class MilestonePlanner:
    def plan(self, project_goal: str) -> dict:
        milestones = [
            {"milestone": "define_success_state", "risk": "L0"},
            {"milestone": "map_capabilities", "risk": "L1"},
            {"milestone": "run_sandbox_execution", "risk": "L2"},
            {"milestone": "validate_real_runtime", "risk": "L2"},
            {"milestone": "promote_stable_path", "risk": "L1"},
        ]
        if "外部" in project_goal or "真实" in project_goal:
            milestones.insert(3, {"milestone": "authorize_external_connectors", "risk": "L3"})
        return {"status": "milestones_ready", "milestones": milestones}
