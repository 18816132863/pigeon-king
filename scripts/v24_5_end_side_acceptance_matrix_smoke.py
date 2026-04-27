#!/usr/bin/env python3
"""V24.5 end-side acceptance matrix smoke."""

from __future__ import annotations

import sys
from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import tempfile
from pathlib import Path

from execution.action_idempotency_guard import IdempotencyGuard
from execution.device_receipt_reconciler import reconcile_device_action
from governance.policy.failure_taxonomy import classify_failure
from orchestration.end_side_workflow_contract import compile_three_channel_reminder, assert_serial_order
from orchestration.remediation_planner import plan_remediation
from orchestration.side_effect_transaction import build_three_channel_reminder_transaction
from platform_adapter.alarm_tool_policy import build_alarm_tool_call, should_retry_modify_alarm_without_verify


def main() -> None:
    contract = compile_three_channel_reminder("10:20 吃饭提醒，三种方式都要")
    assert assert_serial_order(contract)
    assert [p.name for p in contract.phases] == ["alarm", "hiboard_push", "chat_cron", "final_verify"]

    search_call = build_alarm_tool_call("search_alarm", {"rangeType": "all"})
    assert search_call.arguments["rangeType"] == "next"
    modify_call = build_alarm_tool_call("modify_alarm", {"entityId": "120", "alarmTime": "20260427 102000", "alarmTitle": "吃饭提醒"})
    assert modify_call.timeout_seconds == 90
    assert should_retry_modify_alarm_without_verify() is False

    expected = {"entityId": "120", "alarmTime": "20260427 102000", "alarmTitle": "吃饭提醒"}
    observed = {"entityId": "120", "alarmTime": "20260427 102000", "alarmTitle": "吃饭提醒"}
    rec = reconcile_device_action(
        action_name="modify_alarm",
        action_result={"status": "timeout"},
        expected_state=expected,
        observed_after_timeout=observed,
    )
    assert rec.status == "success_with_timeout_receipt"
    assert rec.device_state == "connected_but_action_timeout"

    fail = classify_failure({"action": "modify_alarm", "status": "timeout"})
    assert fail.code == "ACTION_TIMEOUT"
    assert fail.device_state == "connected_but_action_timeout"
    plan = plan_remediation(fail)
    assert plan.action == "verify_then_continue"
    assert "do_not_mark_device_offline" in plan.must_avoid

    tx = build_three_channel_reminder_transaction("tx-demo", "吃饭提醒")
    tx.update_step("alarm", "success_with_timeout_receipt", {"entityId": "120"})
    tx.update_step("hiboard_push", "success", {"code": "0000000000"})
    tx.update_step("chat_cron", "scheduled", {"channel": "xiaoyi-channel"})
    tx.update_step("final_verify", "success")
    assert tx.overall_status() == "success"

    with tempfile.TemporaryDirectory() as td:
        guard = IdempotencyGuard(Path(td) / "idem.json")
        payload = {"entityId": "120", "alarmTime": "20260427 102000", "alarmTitle": "吃饭提醒"}
        first = guard.reserve("modify_alarm", payload)
        guard.mark(first.action_key, "success_with_timeout_receipt", {"verified": True})
        second = guard.reserve("modify_alarm", payload)
        assert second.action_key == first.action_key
        assert second.status == "success_with_timeout_receipt"
        assert guard.should_execute(second) is False

    print("v24_5_end_side_acceptance_matrix_smoke: pass")


if __name__ == "__main__":
    main()
