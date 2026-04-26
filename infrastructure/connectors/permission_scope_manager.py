class PermissionScopeManager:
    HIGH_RISK_SCOPES = {"send", "delete", "payment", "account", "publish", "call"}

    def evaluate(self, scopes: list[str]) -> dict:
        high = sorted(set(scopes) & self.HIGH_RISK_SCOPES)
        return {
            "status": "requires_approval" if high else "allowed_for_planning",
            "high_risk_scopes": high,
            "least_privilege_required": True,
        }
