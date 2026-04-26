class RollbackManager:
    def build_rollback_plan(self, action_plan: list[dict]) -> dict:
        return {
            "status": "rollback_plan_ready",
            "steps": [
                {"for_step": idx, "rollback": "restore_previous_state_or_disable_experimental_capability"}
                for idx, _ in enumerate(action_plan)
            ],
            "requires_snapshot": True,
        }
