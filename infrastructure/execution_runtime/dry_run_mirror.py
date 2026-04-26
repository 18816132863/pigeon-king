class DryRunMirror:
    def mirror(self, action: dict) -> dict:
        return {
            "status": "dry_run_ready",
            "action": action,
            "side_effect": False,
            "would_execute": action.get("action_id", "unknown"),
        }
