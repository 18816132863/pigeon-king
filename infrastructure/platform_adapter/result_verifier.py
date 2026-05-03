"""V11.8 Result Verifier: normalize and verify runtime action results before completion."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from infrastructure.platform_adapter.runtime_state_store import get_action, transition_action, _now_ms


@dataclass
class VerificationResult:
    action_id: str
    verified: bool
    status: str
    reason: str
    required_missing: list
    result: Dict[str, Any]
    generated_at_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def verify_action_result(
    action_id: str,
    *,
    result: Optional[Dict[str, Any]] = None,
    required_fields: Optional[Iterable[str]] = None,
    allow_uncertain: bool = False,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    action = get_action(action_id, db_path=db_path)
    if not action:
        raise KeyError(f"unknown action_id: {action_id}")
    result = result or {}
    required = list(required_fields or [])
    missing = [field for field in required if field not in result or result.get(field) in (None, "")]
    uncertain = bool(result.get("uncertain") or result.get("status") in {"unknown", "timeout", "partial"})

    if missing:
        status = "hold_for_result_check"
        verified = False
        reason = "result_missing_required_fields"
    elif uncertain and not allow_uncertain:
        status = "hold_for_result_check"
        verified = False
        reason = "result_uncertain_requires_probe_check"
    elif result.get("ok") is False:
        status = "failed"
        verified = False
        reason = str(result.get("error") or "adapter_reported_failure")
    else:
        status = "completed"
        verified = True
        reason = "result_verified"

    transition_action(action_id, status, reason=reason, result={"verified": verified, "result": result}, error=None if verified else reason, db_path=db_path)
    return VerificationResult(action_id, verified, status, reason, missing, result, _now_ms()).to_dict()


def build_result_contract(*, capability: str, op_name: str, side_effecting: bool = True) -> Dict[str, Any]:
    base_required = ["ok", "status"]
    if side_effecting:
        base_required.append("receipt")
    return {
        "capability": capability,
        "op_name": op_name,
        "required_fields": base_required,
        "uncertain_statuses": ["unknown", "timeout", "partial"],
        "completion_rule": "required_fields_present_and_not_uncertain",
    }
