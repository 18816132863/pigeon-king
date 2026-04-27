from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.constitutional_judge_v4 import ConstitutionalJudgeV4
j = ConstitutionalJudgeV4()
d = j.judge("device_action", {"side_effect": True, "device_side_effect": True})
assert d.decision == "allow"
assert "global_device_serial_lane" in d.required_controls
danger = j.judge("unknown_code_install", {"sandboxed": False})
assert danger.decision == "deny"
print("v30_0_constitutional_judge_smoke: pass")
