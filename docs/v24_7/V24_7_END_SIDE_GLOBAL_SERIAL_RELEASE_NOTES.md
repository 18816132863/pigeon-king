# V24.7 End-side Global Serial Executor

V24.7 turns the previous reminder-only serial rule into a global end-side rule:

> Any multi-action workflow that touches device-side capabilities must route device actions through one serial lane.

Applies to alarm, notification, calendar, GUI action, file, app action, settings, and generic device tool calls.

Device actions run as:

```text
acquire_device_lock
→ execute_one_device_action
→ verify_result_or_pending_verify
→ write_action_receipt
→ release_device_lock
→ next_action
```

Rules:
- Pure local computation can run outside the device lane.
- Device-side actions cannot run in parallel with other device-side actions within the same goal / transaction / device session.
- Timeout is classified as `timeout_pending_verify`; it must not become `device_offline` unless a separate connectivity probe proves offline.
- All actions require `action_id`, `idempotency_key`, timeout profile, verification policy, and receipt.

Validation:

```bash
/usr/bin/python3 scripts/v24_7_end_side_global_serial_smoke.py
/usr/bin/python3 scripts/v24_7_end_side_global_serial_gate.py
```
