# V24.8 - V25.7 Advance Notes

This is an incremental advance pack on top of V24.7.

## Small issues closed first

- V24.8: hard global end-side serial gate.
- V24.9: pending verification dependency barrier.
- V25.0: timeout receipt verifier; action timeout no longer means device offline.
- V25.1: six-layer integrity gate; agent_kernel stays in L3.

## Continued plan

- V25.2: Goal Contract V2.
- V25.3: Durable Task Graph V2.
- V25.4: Memory Writeback Guard V2.
- V25.5: World Interface Resolver V2.
- V25.6: Capability Extension Sandbox Gate V2.
- V25.7: Personal Operating Agent Loop V2 and gate.

## Run

```bash
/usr/bin/python3 scripts/v24_8_to_v25_7_all_smoke.py
/usr/bin/python3 scripts/v25_7_personal_operating_agent_gate.py
```
