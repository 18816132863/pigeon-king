#!/usr/bin/env python3
from pathlib import Path
import runpy
import sys
import json
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

scripts = [
    "v24_8_end_side_hard_serial_smoke.py",
    "v24_9_device_dependency_barrier_smoke.py",
    "v25_0_device_timeout_receipt_verifier_smoke.py",
    "v25_1_layer_integrity_gate_smoke.py",
    "v25_2_goal_contract_smoke.py",
    "v25_3_task_graph_smoke.py",
    "v25_4_memory_writeback_guard_smoke.py",
    "v25_5_world_interface_resolver_smoke.py",
    "v25_6_capability_extension_sandbox_gate_smoke.py",
    "v25_7_personal_operating_loop_smoke.py",
]

passed = []
for script in scripts:
    runpy.run_path(str(ROOT / "scripts" / script), run_name="__main__")
    passed.append(script)

report = {
    "status": "pass",
    "range": "V24.8-V25.7",
    "passed": passed,
    "count": len(passed),
    "updated_at": time.time(),
}
(ROOT / "V24_8_TO_V25_7_ALL_SMOKE_REPORT.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("v24_8_to_v25_7_all_smoke: pass")
