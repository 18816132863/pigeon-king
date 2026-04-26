class ExtensionLifecycleManager:
    STAGES = ["discovered", "evaluated", "sandboxed", "tested", "approved", "experimental", "active"]

    def next_stage(self, current: str, approval: bool = False) -> dict:
        if current == "approved" and not approval:
            return {"status": "blocked", "reason": "approval_required"}
        if current not in self.STAGES:
            return {"status": "rejected", "reason": "unknown_stage"}
        idx = self.STAGES.index(current)
        if idx >= len(self.STAGES) - 1:
            return {"status": "stable", "stage": current}
        return {"status": "advanced", "from": current, "to": self.STAGES[idx + 1]}
