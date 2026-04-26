class ContextRefreshPlanner:
    """Plan which context sources should be refreshed before decisions."""

    def plan(self, goal: str, stale_sources: list[str] | None = None) -> dict:
        stale_sources = stale_sources or []
        required = ["personal_preferences", "recent_goals", "risk_policy"]
        if any(k in goal for k in ["外部", "API", "设备", "连接"]):
            required.append("connector_state")
        if "长期" in goal or "项目" in goal:
            required.append("goal_portfolio")
        refresh = sorted(set(required + stale_sources))
        return {"status": "refresh_plan_ready", "sources": refresh, "side_effect": False}
