from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.operating_contract_v3 import GoalContractCompilerV3
c = GoalContractCompilerV3().compile("明天早上8点提醒我吃饭，三种方式都要")
assert c.contract_id.startswith("goal_")
assert c.risk_boundary in ("L1", "L2", "L3", "L4")
assert "device_capability_bus" in c.information_sources
print("v26_0_goal_governance_smoke: pass")
