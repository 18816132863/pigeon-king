# V12.1 → V12.5 Advance Notes

Continue from V12.0 without redesigning the six-layer architecture.

| Version | Capability | Purpose |
|---|---|---|
| V12.1 | Trace Recorder | Local correlation trace for action diagnosis |
| V12.2 | Replay Harness | Deterministic regression replay |
| V12.3 | Snapshot Manager | SQLite snapshot and rollback verification |
| V12.4 | SLO Monitor | Stale running / blocked / leased queue gate |
| V12.5 | Upgrade Orchestrator | Final gate report for V12.1-V12.5 |

Run:

```bash
/usr/bin/python3 scripts/v12_1_to_v12_5_all_smoke.py
```
