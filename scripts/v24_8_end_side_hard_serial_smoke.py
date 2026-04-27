#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestration.end_side_hard_serial_gate import EndSideAction, EndSideHardSerialGate

gate = EndSideHardSerialGate()
actions = [
    EndSideAction("a1", "alarm", "modify_alarm", idempotency_key="k1", timeout_profile="modify_alarm_90s", verification_policy="post_verify"),
    EndSideAction("a2", "calendar", "create_event", idempotency_key="k2", timeout_profile="calendar_60s", verification_policy="post_verify"),
    EndSideAction("l1", "local_compute", "summarize", idempotency_key="k3"),
]
plan = gate.normalize("goal_demo", actions)
assert [a.action_id for a in plan.serial_device_actions] == ["a1", "a2"]
assert [a.action_id for a in plan.non_device_actions] == ["l1"]
print("v24_8_end_side_hard_serial_smoke: pass")
