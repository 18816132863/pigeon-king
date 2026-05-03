"""Maturity scorecard for the one-final-switch-away target shape."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping

@dataclass
class PendingAccessMaturityScore:
    status: str
    score: float
    level: str
    passed: int
    total: int
    checks: List[Dict[str, Any]]
    missing: List[str]
    final_switch_statement: str
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class PendingAccessMaturityScorecard:
    REQUIRED = [
        "goal_compiler", "long_horizon_planner", "action_semantics", "commit_barrier",
        "freeze_switch", "mock_contract_registry", "world_model_or_digital_twin",
        "shadow_replay", "memory_governance", "capability_gap_detector",
        "skill_extension_sandbox", "audit_replay", "risk_tier_matrix",
        "real_execution_broker_hardened", "approval_pack_generation",
        "live_adapter_contracts_declared", "payment_signature_physical_hard_stop",
    ]
    def evaluate(self, manifest: Mapping[str, Any] | None = None) -> PendingAccessMaturityScore:
        manifest = dict(manifest or {})
        modules = set(manifest.get("modules", []))
        checks: List[Dict[str, Any]] = []
        missing: List[str] = []
        for item in self.REQUIRED:
            ok = item in modules or manifest.get(item) is True
            checks.append({"name": item, "ok": ok})
            if not ok:
                missing.append(item)
        no_live = manifest.get("real_world_connected") is False and manifest.get("real_side_effect_allowed") is False
        checks.append({"name": "real_world_live_switch_closed", "ok": no_live})
        if not no_live:
            missing.append("real_world_live_switch_must_be_closed")
        final_switch = manifest.get("final_switch_limited_to") in {"adapter_credential_approval_config", "adapter/credential/approval"}
        checks.append({"name": "final_switch_limited_to_adapter_credential_approval", "ok": final_switch})
        if not final_switch:
            missing.append("final_switch_scope_not_proven")
        passed = sum(1 for c in checks if c.get("ok"))
        total = len(checks)
        score = round(passed / total, 4) if total else 0.0
        if score >= 0.95 and not missing:
            status, level = "pass", "V77_pending_access_complete"
        elif score >= 0.80:
            status, level = "partial", "near_pending_access_complete"
        else:
            status, level = "fail", "insufficient"
        return PendingAccessMaturityScore(status, score, level, passed, total, checks, missing, "only_live_adapter_credentials_and_approval_configuration_remain" if final_switch else "not_yet_one_switch_away")

def evaluate_pending_access_maturity(manifest: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    return PendingAccessMaturityScorecard().evaluate(manifest).to_dict()
