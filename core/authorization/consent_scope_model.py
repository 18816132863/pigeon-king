class ConsentScopeModel:
    HIGH_RISK = {"send", "delete", "publish", "payment", "account", "call", "install"}

    def evaluate(self, scopes: list[str]) -> dict:
        high = sorted(set(scopes) & self.HIGH_RISK)
        return {
            "status": "evaluated",
            "scopes": scopes,
            "high_risk_scopes": high,
            "least_privilege": True,
            "requires_explicit_consent": bool(high),
        }
