"""Readiness gate for the 'full-function pending access' AI shape."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .action_semantics import COMMIT_CLASSES, HARD_STOP_CLASSES, default_action_catalog
from .commit_barrier import CommitBarrier
from .freeze_switch import assert_pending_access_frozen


@dataclass(frozen=True)
class ReadinessGateResult:
    status: str
    score: float
    passed_checks: int
    total_checks: int
    checks: List[Dict[str, Any]]
    missing: List[str]
    next_gate: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PendingAccessReadinessGate:
    REQUIRED_MODULES = [
        "goal_compiler", "long_horizon_planner", "personal_memory", "world_model_or_digital_twin",
        "skill_interface_layer", "sandbox_executor", "verifier", "commit_barrier", "audit_replay",
        "mock_contract_registry", "shadow_mode", "capability_gap_loop",
    ]

    def evaluate(self, manifest: Mapping[str, Any] | None = None) -> ReadinessGateResult:
        manifest = dict(manifest or {})
        checks: List[Dict[str, Any]] = []
        missing: List[str] = []

        modules = set(manifest.get("modules", []))
        for module in self.REQUIRED_MODULES:
            ok = module in modules or manifest.get(module) is True
            checks.append({"name": f"module:{module}", "ok": ok})
            if not ok:
                missing.append(module)

        catalog = manifest.get("action_catalog") or default_action_catalog()
        catalog_ok = len(catalog) >= 100
        checks.append({"name": "action_semantics_catalog_100_plus", "ok": catalog_ok, "count": len(catalog)})
        if not catalog_ok:
            missing.append("100_plus_action_semantics_catalog")

        barrier = CommitBarrier()
        payment_block = not barrier.check({"op_name": "checkout_order", "payment": True}).allowed
        physical_block = not barrier.check({"op_name": "move_robot", "physical_actuation": True}).allowed
        external_block = not barrier.check({"op_name": "send_email", "payload": {"recipient": "x"}}).allowed
        observe_allow = barrier.check({"op_name": "query_calendar"}).allowed
        for name, ok in [
            ("payment_hard_cutoff", payment_block),
            ("physical_actuation_hard_cutoff", physical_block),
            ("external_send_commit_stop", external_block),
            ("observe_reason_prepare_allowed", observe_allow),
        ]:
            checks.append({"name": name, "ok": ok})
            if not ok:
                missing.append(name)

        frozen = assert_pending_access_frozen(manifest.get("live_switches"))
        checks.append({"name": "live_switches_frozen", "ok": frozen["ok"], "detail": frozen})
        if not frozen["ok"]:
            missing.append("live_switches_must_be_closed")

        total = len(checks)
        passed = sum(1 for c in checks if c.get("ok"))
        score = passed / total if total else 0.0
        status = "pass" if not missing else "partial"
        return ReadinessGateResult(
            status=status,
            score=round(score, 4),
            passed_checks=passed,
            total_checks=total,
            checks=checks,
            missing=missing,
            next_gate="shadow_replay_and_mock_contract_coverage" if status == "pass" else "complete_missing_modules",
        )
