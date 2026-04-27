from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.autonomy_regression_matrix_v4 import AutonomyRegressionMatrixV4
m = AutonomyRegressionMatrixV4()
res = m.evaluate({
    "contract_id": "x", "risk_boundary": "L2", "done_definition": ["d"],
    "global_device_serial": True, "pending_verify_blocks_dependent": True,
    "judge_decision": "allow", "required_controls": ["audit"],
    "memory_status": "written", "pollution_prevented": True,
    "gap_detected": True, "sandbox_required": True, "rollback_required": True,
})
assert res["pass"]
print("v33_0_autonomy_regression_smoke: pass")
