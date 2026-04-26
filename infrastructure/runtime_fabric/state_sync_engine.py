class StateSyncEngine:
    def sync_plan(self, states: list[str]) -> dict:
        return {
            "status": "sync_plan_ready",
            "states": states,
            "conflict_policy": "newer_verified_state_wins",
            "requires_audit": True,
        }
