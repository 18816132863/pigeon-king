# V23.7 → V24.6 Advance Notes

This package continues from V23.6 and adds ten incremental versions. It is an
overlay package, not a clean full merge package.

## Version map

| Version | Layer | Capability |
|---|---|---|
| V23.7 | L4 Execution | Action idempotency guard |
| V23.8 | L4 Execution | Device receipt reconciler |
| V23.9 | L4 / Platform Adapter | Alarm tool policy |
| V24.0 | L3 Orchestration | Side-effect transaction model |
| V24.1 | L3 Orchestration | End-side workflow contract |
| V24.2 | L6 Infrastructure | Progress heartbeat |
| V24.3 | L5 Governance | Failure taxonomy |
| V24.4 | L3 Orchestration | Remediation planner |
| V24.5 | Acceptance | End-side acceptance matrix |
| V24.6 | L6 Infrastructure | End-side stability gate |

## Fixed rules

1. `agent_kernel` remains an L3 Orchestration center, not L7.
2. Device-connected does not equal action-success.
3. `modify_alarm` timeout does not mean device offline.
4. After `modify_alarm` timeout, run targeted verification before retry.
5. `search_alarm` defaults to `rangeType=next`; do not use `all` by default.
6. Multi-channel reminder execution must be serial: alarm → Hiboard → chat cron → final verify.
7. Side-effect actions must be idempotency-protected.
8. Long tasks must write heartbeat/progress state.

## Commands

```bash
/usr/bin/python3 scripts/v23_7_to_v24_6_all_smoke.py
/usr/bin/python3 scripts/v24_6_end_side_stability_gate.py
```
