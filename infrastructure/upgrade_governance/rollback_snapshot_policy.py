class RollbackSnapshotPolicy:
    def require_snapshot(self, upgrade: dict) -> dict:
        return {
            "status": "snapshot_required",
            "before_upgrade": True,
            "after_upgrade": True,
            "rollback_command_required": True,
            "reason": upgrade.get("target", "unknown"),
        }
