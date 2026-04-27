from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.operating_contract_v3 import GoalContractCompilerV3
from orchestration.durable_workflow_engine_v3 import DurableWorkflowCompilerV3
c = GoalContractCompilerV3().compile("设置闹钟提醒并写回经验")
g = DurableWorkflowCompilerV3().build_from_contract(c)
assert g.assert_device_actions_serialized()
assert any(n.device_side_effect for n in g.nodes)
print("v27_0_durable_workflow_smoke: pass")
