from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from personality.persona_drift_guard_v4 import PersonaDriftGuardV4
g = PersonaDriftGuardV4()
ok = g.check_response_plan({"creates_L7": False, "long_task_without_state": False})
bad = g.check_response_plan({"creates_L7": True})
assert ok["pass"]
assert not bad["pass"]
print("v34_0_persona_drift_guard_smoke: pass")
