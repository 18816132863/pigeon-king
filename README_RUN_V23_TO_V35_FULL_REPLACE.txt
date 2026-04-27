V23.1 -> V35.0 FULL REPLACE RELEASE

This package is a full replacement package, not an incremental patch.
It is based on the V10.9->V23.1 full release and includes V23.2->V35.0 outputs.

Usage:
cd pigeon_king_v10_9
/usr/bin/python3 scripts/v23_to_v35_full_replace_gate.py
/usr/bin/python3 scripts/v26_0_to_v35_0_all_smoke.py
/usr/bin/python3 scripts/v35_0_autonomous_os_gate.py

Hard rules:
- agent_kernel belongs to L3 Orchestration, not L7.
- All multi-action end-side capabilities must be globally serialized.
- action_timeout must become pending_verify, not device_offline.
- Autonomy must stay under judge, approval, audit, recovery, and memory-writeback boundaries.
