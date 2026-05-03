#!/usr/bin/env python3
"""V23.7 -> V24.6 all smoke gate.

This script is intentionally single-process and stdlib-only except for local
modules, to avoid subprocess hangs in compacted/long-context environments.
"""

from __future__ import annotations

import sys
from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import json
import tempfile
from pathlib import Path

from core.release_manifest_v23_7_to_v24_6 import VERSIONS, assert_no_new_layer, version_names
from execution.action_idempotency_guard import IdempotencyGuard
from execution.device_receipt_reconciler import reconcile_device_action
from governance.policy.failure_taxonomy import classify_failure
from infrastructure.progress_heartbeat import ProgressHeartbeat
from orchestration.end_side_workflow_contract import compile_three_channel_reminder, assert_serial_order
from orchestration.remediation_planner import plan_remediation
from orchestration.side_effect_transaction import build_three_channel_reminder_transaction
from infrastructure.platform_adapter.alarm_tool_policy import build_alarm_tool_call, normalize_search_alarm_args


def run_all() -> dict:
    results = {}

    results["manifest_versions"] = version_names()
    assert len(VERSIONS) == 10
    assert assert_no_new_layer() is True

    normalized = normalize_search_alarm_args({"rangeType": "all"})
    assert normalized["rangeType"] == "next"
    modify = build_alarm_tool_call("modify_alarm", {"entityId": "120", "alarmTitle": "吃饭提醒", "alarmTime": "20260427 102000"})
    assert modify.timeout_seconds == 90
    results["alarm_policy"] = "pass"

    expected = {"entityId": "120", "alarmTitle": "吃饭提醒", "alarmTime": "20260427 102000"}
    observed = {"entityId": "120", "alarmTitle": "吃饭提醒", "alarmTime": "20260427 102000"}
    reconciled = reconcile_device_action(
        action_name="modify_alarm",
        action_result={"status": "timeout"},
        expected_state=expected,
        observed_after_timeout=observed,
    )
    assert reconciled.status == "success_with_timeout_receipt"
    assert reconciled.device_state == "connected_but_action_timeout"
    results["receipt_reconcile"] = reconciled.status

    failure = classify_failure({"action": "modify_alarm", "status": "timeout"})
    assert failure.code == "ACTION_TIMEOUT"
    plan = plan_remediation(failure)
    assert plan.action == "verify_then_continue"
    results["failure_remediation"] = plan.action

    contract = compile_three_channel_reminder("提醒我吃饭，三种方式都要")
    assert assert_serial_order(contract)
    assert [p.name for p in contract.phases] == ["alarm", "hiboard_push", "chat_cron", "final_verify"]
    results["workflow_contract"] = "serial"

    tx = build_three_channel_reminder_transaction("tx-v24", "吃饭提醒")
    tx.update_step("alarm", "success_with_timeout_receipt")
    tx.update_step("hiboard_push", "success")
    tx.update_step("chat_cron", "scheduled")
    tx.update_step("final_verify", "success")
    assert tx.overall_status() == "success"
    results["transaction"] = tx.overall_status()

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        guard = IdempotencyGuard(td_path / "idempotency.json")
        payload = {"entityId": "120", "alarmTitle": "吃饭提醒", "alarmTime": "20260427 102000"}
        rec1 = guard.reserve("modify_alarm", payload)
        guard.mark(rec1.action_key, "running")
        rec2 = guard.reserve("modify_alarm", payload)
        assert rec2.status == "running"
        assert guard.should_execute(rec2) is False

        hb = ProgressHeartbeat(td_path / "task_state" / "current_task_state.json")
        state = hb.write(
            task_id="task-v24",
            current_phase="alarm",
            completed_steps=[],
            pending_steps=["alarm", "hiboard_push", "chat_cron", "final_verify"],
            next_command="/usr/bin/python3 scripts/resume_current_task.py",
            metadata={"release": "V24.6"},
        )
        assert hb.read().task_id == state.task_id
        assert hb.is_stale(max_age_seconds=999999) is False

    results["idempotency"] = "pass"
    results["heartbeat"] = "pass"
    results["v23_7_to_v24_6_all_smoke"] = "pass"
    return results


def main() -> None:
    results = run_all()
    report_path = Path("V23_7_TO_V24_6_SMOKE_REPORT.json")
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print("v23_7_to_v24_6_all_smoke: pass")
    print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
