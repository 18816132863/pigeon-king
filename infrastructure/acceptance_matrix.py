"""V11.9 Acceptance Matrix: deterministic smoke scenarios for runtime execution safety."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from governance.policy.execution_autopilot import plan_runtime_action
from platform_adapter.runtime_state_store import register_action, enqueue_action, summarize_runtime
from platform_adapter.delivery_outbox import lease_next, mark_failed, outbox_summary
from platform_adapter.result_verifier import build_result_contract, verify_action_result
from platform_adapter.recovery_manager import recover_stale_actions


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _scenario_low_risk_direct(db_path: Optional[Path]) -> ScenarioResult:
    d = plan_runtime_action(capability="search", op_name="lookup", payload={"q": "ping"}, risk_level="L1", db_path=db_path)
    return ScenarioResult("low_risk_direct", d["status"] == "allowed", d)


def _scenario_high_risk_confirmation(db_path: Optional[Path]) -> ScenarioResult:
    d = plan_runtime_action(capability="MESSAGE_SENDING", op_name="send", payload={"to": "demo", "body": "hello"}, risk_level="L3", db_path=db_path)
    return ScenarioResult("high_risk_requires_confirmation", d["status"] in {"requires_confirmation", "queued"}, d)


def _scenario_outbox_uncertain_timeout(db_path: Optional[Path]) -> ScenarioResult:
    action = register_action(capability="MESSAGE_SENDING", op_name="send", payload={"body": "timeout"}, risk_level="L2", db_path=db_path)
    qid = enqueue_action(action.action_id, delivery_mode="confirm_then_queue", db_path=db_path)
    leased = lease_next(limit=1, db_path=db_path)
    failed = mark_failed(qid, error="timeout", side_effecting=True, result_uncertain=True, db_path=db_path)
    return ScenarioResult("side_effect_timeout_blocks_retry", failed["status"] == "blocked" and bool(leased), {"leased": leased, "failed": failed})


def _scenario_result_contract(db_path: Optional[Path]) -> ScenarioResult:
    action = register_action(capability="file_write", op_name="write", payload={"path": "demo.txt"}, risk_level="L1", db_path=db_path)
    contract = build_result_contract(capability="file_write", op_name="write", side_effecting=True)
    verified = verify_action_result(action.action_id, result={"ok": True, "status": "done", "receipt": "local:demo"}, required_fields=contract["required_fields"], db_path=db_path)
    return ScenarioResult("result_contract_completion", verified["verified"] is True and verified["status"] == "completed", verified)


def _scenario_recovery(db_path: Optional[Path]) -> ScenarioResult:
    action = register_action(capability="search", op_name="stale_lookup", payload={"q": "recover"}, risk_level="L1", db_path=db_path)
    # Make it look stale in a deterministic way.
    from platform_adapter.runtime_state_store import connect
    with connect(db_path) as conn:
        conn.execute("UPDATE runtime_actions SET state='running', updated_at_ms=1 WHERE action_id=?", (action.action_id,))
    report = recover_stale_actions(stale_after_ms=1_000, db_path=db_path).to_dict()
    return ScenarioResult("stale_running_recovery", report["recovered"] >= 1, report)


def run_acceptance_matrix(db_path: Optional[Path] = None) -> Dict[str, Any]:
    scenarios: List[Callable[[Optional[Path]], ScenarioResult]] = [
        _scenario_low_risk_direct,
        _scenario_high_risk_confirmation,
        _scenario_outbox_uncertain_timeout,
        _scenario_result_contract,
        _scenario_recovery,
    ]
    results = [scenario(db_path).to_dict() for scenario in scenarios]
    passed = sum(1 for r in results if r["passed"])
    return {
        "gate": "pass" if passed == len(results) else "fail",
        "passed": passed,
        "total": len(results),
        "results": results,
        "runtime": summarize_runtime(db_path=db_path),
        "outbox": outbox_summary(db_path=db_path),
    }
