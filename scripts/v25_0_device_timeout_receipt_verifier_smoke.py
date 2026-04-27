#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from execution.device_timeout_receipt_verifier_v2 import DeviceTimeoutReceiptVerifierV2

verifier = DeviceTimeoutReceiptVerifierV2()
outcome = verifier.verify_after_timeout(
    action_id="alarm_modify",
    action_name="modify_alarm",
    device_connected=True,
    verification_probe=lambda: {"alarmTime": "20260427 102000", "alarmTitle": "吃饭提醒"},
    expected={"alarmTime": "20260427 102000", "alarmTitle": "吃饭提醒"},
)
assert outcome.device_status == "connected_but_action_timeout"
assert outcome.action_status == "success_with_timeout_receipt"
assert outcome.retry_allowed is False
print("v25_0_device_timeout_receipt_verifier_smoke: pass")
