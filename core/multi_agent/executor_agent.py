class ExecutorAgent:
    """Execution stub: returns execution readiness, not real side effects."""

    def prepare(self, plan: dict) -> dict:
        return {
            "status": "execution_prepared",
            "side_effect": False,
            "real_execution_requires_route_runtime": True,
            "requires_confirmation": bool(plan.get("requires_confirmation")),
        }
