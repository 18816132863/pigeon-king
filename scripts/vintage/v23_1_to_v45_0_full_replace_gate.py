from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
required=['scripts/v23_to_v35_full_replace_gate.py','scripts/v35_0_autonomous_os_gate.py','scripts/v36_0_to_v45_0_all_smoke.py','scripts/v45_0_autonomous_os_supreme_gate.py','core/personal_os_v36_v45/operating_organs.py']
missing=[p for p in required if not (ROOT/p).exists()]
assert not missing, {'missing':missing}
print({'v23_1_to_v45_0_full_replace_gate':'pass','required':len(required)})
