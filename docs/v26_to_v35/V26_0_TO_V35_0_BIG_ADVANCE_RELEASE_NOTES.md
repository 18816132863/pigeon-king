# V26.0 → V35.0 Big Advance Release Notes

This is an incremental advance pack to be overlaid on the current V25.7 project.

## Version plan

| Version | Big advance |
|---|---|
| V26.0 | Operating Contract V3: one-sentence goal → governed objective contract |
| V27.0 | Durable Workflow Engine V3: task graph, dependency, resume, serial device nodes |
| V28.0 | End-side Serial Lanes V3: global device action serialization and idempotency |
| V29.0 | Personal Memory Kernel V4: semantic / episodic / procedural / preference guarded memory |
| V30.0 | Constitutional Judge V4: hard law + soft preference + situational controls |
| V31.0 | Universal World Resolver V4: local / device / connector / API / MCP-like capability resolution |
| V32.0 | Controlled Extension Pipeline V4: gap detection, sandbox gate, rollback and promotion |
| V33.0 | Autonomy Regression Matrix V4: autonomous-agent regression checks |
| V34.0 | Persona Drift Guard V4: prevents L7 drift, unsafe autonomy, and weak state behavior |
| V35.0 | Autonomous OS Mission Control V4: top-level autonomous operating gate |

## Architecture rule

Still six layers only:

- L1 Core
- L2 Memory Context
- L3 Orchestration
- L4 Execution
- L5 Governance
- L6 Infrastructure

`agent_kernel` / autonomous organ remains an L3 orchestration hub, not L7.

## Commands

```bash
/usr/bin/python3 scripts/v26_0_to_v35_0_all_smoke.py
/usr/bin/python3 scripts/v35_0_autonomous_os_gate.py
```
