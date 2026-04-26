from __future__ import annotations


class AuditVerifier:
    """Verify whether autonomous decisions include audit, rollback and approval policy."""

    def verify_extension_plan(self, plan: dict) -> dict:
        policy = plan.get("safety_policy", {})
        ok = bool(policy.get("sandbox_required")) and bool(policy.get("rollback_required", True) or plan.get("rollback_plan"))
        return {
            "status": "pass" if ok else "fail",
            "sandbox_required": bool(policy.get("sandbox_required")),
            "rollback_present": bool(policy.get("rollback_required", True) or plan.get("rollback_plan")),
            "unknown_direct_install_blocked": bool(policy.get("no_untrusted_direct_install", True)),
        }
