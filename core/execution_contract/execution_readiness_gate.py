class ExecutionReadinessGate:
    def check(self, contract: dict) -> dict:
        if contract.get("risk_level") == "BLOCKED":
            return {"status": "blocked", "reason": "blocked_risk"}
        if not contract.get("can_execute_without_confirmation") and not (contract.get("confirmation") or {}).get("confirmed", False):
            return {"status": "waiting_confirmation", "reason": "confirmation_not_recorded"}
        return {"status": "ready", "reason": "contract_satisfied"}
