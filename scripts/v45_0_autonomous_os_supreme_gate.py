import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from core.personal_os_v36_v45.operating_organs import AutonomousOSSupremeGate
report={'six_layer_no_l7':True,'goal_contract_ok':True,'handoff_trace_ok':True,'tool_guardrails_ok':True,'device_saga_serial_ok':True,'capability_extension_sandboxed':True,'scenario_simulation_ok':True,'autonomy_budget_ok':True,'memory_guarded':True,'continuous_evaluation_ok':True,'agent_kernel_layer':'L3','has_l7':False}
result=AutonomousOSSupremeGate().check(report)
assert result['pass'], result
print(result)
