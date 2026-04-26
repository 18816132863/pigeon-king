class SandboxPromotionGate:
    def evaluate(self, test_result: dict, audit: dict, rollback: dict) -> dict:
        ok = bool(test_result.get("success")) and bool(audit.get("audit_required")) and bool(rollback.get("requires_snapshot"))
        return {
            "status": "promote_to_experimental" if ok else "stay_sandboxed",
            "can_be_active": False,
            "requires_user_approval_for_active": True,
        }
