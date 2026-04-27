#!/usr/bin/env python3
"""V23.2 -> V23.6 inline smoke checks.
Run from project root after overlaying this pack.
"""
from __future__ import annotations

import json
from pathlib import Path

from agent_kernel.architecture_boundary import build_architecture_boundary_report, scan_text_for_forbidden_layers
from agent_kernel.hub_boundary_contract import assert_no_boundary_conflict
from execution.device_action_timeout_verifier import (
    normalize_search_alarm_arguments,
    verify_alarm_modify_timeout,
    get_timeout_seconds,
)
from orchestration.device_workflow_serial_policy import normalize_reminder_workflow_order
from infrastructure.compact_resume_policy import build_resume_state
from governance.policy.organ_conflict_policy import check_all_default_organs


def main() -> int:
    checks = []

    arch = build_architecture_boundary_report()
    checks.append(("v23_2_architecture_boundary", arch.passed and arch.agent_kernel_layer == "L3 Orchestration"))
    checks.append(("v23_2_forbidden_l7_scan", not scan_text_for_forbidden_layers("agent_kernel is L3 Orchestration")))

    hub = assert_no_boundary_conflict([
        "receive_goal",
        "compile_goal",
        "build_task_graph",
        "request_risk_decision",
        "request_execution",
        "request_memory_write",
        "request_recovery",
    ])
    checks.append(("v23_3_hub_boundary", hub["passed"]))

    search_args = normalize_search_alarm_arguments({"rangeType": "all"})
    checks.append(("v23_4_search_alarm_no_all", search_args.get("rangeType") == "next"))
    checks.append(("v23_4_modify_timeout_profile", get_timeout_seconds("modify_alarm") == 90))

    desired = {"alarmTime": "20260427 102000", "alarmTitle": "吃饭提醒", "entityId": "120"}
    result = verify_alarm_modify_timeout(desired, lambda _: dict(desired))
    checks.append(("v23_4_timeout_success_receipt", result.state == "success_with_timeout_receipt"))
    checks.append(("v23_4_device_not_offline", result.device_status == "connected_but_action_timeout"))

    order = normalize_reminder_workflow_order(["chat_cron", "alarm", "final_verify", "hiboard_push"])
    checks.append(("v23_4_serial_order", order[:4] == ["alarm", "hiboard_push", "chat_cron", "final_verify"]))

    resume = build_resume_state("smoke", "V23.5", "compact_resume", ["a", "b"])
    resume.mark_complete("a")
    checks.append(("v23_5_no_repeat_completed", "a" in resume.completed_steps and "a" not in resume.pending_steps))

    organs = check_all_default_organs()
    checks.append(("v23_6_organ_conflict_policy", organs["passed"]))

    passed = all(ok for _, ok in checks)
    report = {"v23_2_to_v23_6_all_smoke": "pass" if passed else "fail", "checks": [{"name": n, "passed": ok} for n, ok in checks]}
    Path("V23_2_TO_V23_6_ALL_SMOKE_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
