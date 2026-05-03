"""Deployment preflight gate for the one-final-switch-away state."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping


@dataclass
class PreflightGateResult:
    status: str
    score: float
    checks: Dict[str, bool]
    release_level: str
    final_switch_scope: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PreflightGate:
    def evaluate(self, mission: Mapping[str, Any]) -> PreflightGateResult:
        runtime = mission.get("runtime") or {}
        proofs = mission.get("risk_proofs") or {}
        rollback = mission.get("rollback_plan") or {}
        matrix = mission.get("capability_matrix") or {}
        audit = runtime.get("audit_ledger") or {}
        checks = {
            "runtime_ready": runtime.get("status") == "autonomous_pending_runtime_ready",
            "risk_proofs_pass": proofs.get("status") == "pass" and proofs.get("all_obligations_satisfied") is True,
            "rollback_plan_complete": rollback.get("status") == "rollback_plan_ready" and rollback.get("all_commit_actions_mock_only") is True,
            "capability_matrix_pass": matrix.get("status") == "pass" and matrix.get("score", 0.0) >= 0.90,
            "audit_replayable": audit.get("replayable") is True and audit.get("real_side_effects") == 0,
            "no_live_world_connection": mission.get("real_world_connected") is False,
            "no_real_side_effects": mission.get("real_side_effects") == 0,
            "payment_signature_physical_hard_stopped": mission.get("invariants", {}).get("payment_signature_physical_hard_stop") is True,
            "external_send_draft_or_approval_only": mission.get("invariants", {}).get("external_send_draft_only") is True,
            "final_switch_limited": mission.get("final_switch_scope") == "adapter_credential_approval_config_only",
        }
        score = round(sum(1 for ok in checks.values() if ok) / max(len(checks), 1), 4)
        status = "pass" if all(checks.values()) else "fail"
        release_level = "V79_pre_live_release_candidate" if status == "pass" else "blocked_before_pre_live_release"
        return PreflightGateResult(status, score, checks, release_level, "adapter + credential + approval config only")


def run_preflight_gate(mission: Mapping[str, Any]) -> Dict[str, Any]:
    return PreflightGate().evaluate(mission).to_dict()
