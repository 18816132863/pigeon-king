from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import runpy
scripts = [
    "v26_0_goal_governance_smoke.py",
    "v27_0_durable_workflow_smoke.py",
    "v28_0_end_side_serial_lane_smoke.py",
    "v29_0_personal_memory_smoke.py",
    "v30_0_constitutional_judge_smoke.py",
    "v31_0_world_resolver_smoke.py",
    "v32_0_extension_pipeline_smoke.py",
    "v33_0_autonomy_regression_smoke.py",
    "v34_0_persona_drift_guard_smoke.py",
    "v35_0_autonomous_os_gate.py",
]
for script in scripts:
    runpy.run_path(str(ROOT / "scripts" / script), run_name="__main__")
print("v26_0_to_v35_0_all_smoke: pass")
