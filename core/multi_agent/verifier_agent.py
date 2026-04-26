class VerifierAgent:
    """Build verification checks for planned actions."""

    def verify_plan(self, plan: dict) -> dict:
        checks = ["policy_gate", "result_check", "rollback_available", "audit_written"]
        if plan.get("requires_confirmation"):
            checks.append("strong_confirmation_recorded")
        return {"status": "verification_plan_ready", "checks": checks}
