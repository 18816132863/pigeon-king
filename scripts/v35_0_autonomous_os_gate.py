from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from ops.autonomous_os_mission_control_v4 import AutonomousOSMissionControlV4
result = AutonomousOSMissionControlV4().run_gate()
out = ROOT / "V35_0_AUTONOMOUS_OS_GATE_REPORT.json"
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
assert result["autonomous_os_gate"] == "pass", result
print("v35_0_autonomous_os_gate: pass")
print(str(out))
