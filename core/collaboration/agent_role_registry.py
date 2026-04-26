class AgentRoleRegistry:
    """Define internal roles for multi-agent reasoning without spawning unsafe actors."""

    DEFAULT_ROLES = {
        "strategist": {"capabilities": ["goal_strategy", "risk_reward"], "side_effect": False},
        "critic": {"capabilities": ["assumption_check", "contradiction_detection"], "side_effect": False},
        "operator": {"capabilities": ["execution_preparation", "tool_selection"], "side_effect": False},
        "verifier": {"capabilities": ["result_check", "rollback_check"], "side_effect": False},
        "learner": {"capabilities": ["memory_update", "pattern_promotion"], "side_effect": False},
    }

    def list_roles(self) -> dict:
        return {"status": "roles_ready", "roles": self.DEFAULT_ROLES}

    def get(self, role: str) -> dict:
        return self.DEFAULT_ROLES.get(role, {"capabilities": [], "side_effect": False})
