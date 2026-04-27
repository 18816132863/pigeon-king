#!/usr/bin/env python3
from pathlib import Path
import json, shutil
ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "scripts/v23_1_to_v55_0_full_replace_gate.py",
    "scripts/v46_0_to_v55_0_all_smoke.py",
    "scripts/v56_0_to_v65_0_all_smoke.py",
    "scripts/v65_0_self_evolving_operating_agent_gate.py",
    "agent_kernel/v56_to_v65_operating_agent.py",
    "execution/device_serial_lane_v6.py",
    "memory_context/personal_memory_lifecycle_v6.py",
    "governance/policy/autonomy_safety_case_v6.py",
]
def main():
    for p in list(ROOT.rglob("__pycache__")):
        shutil.rmtree(p, ignore_errors=True)
    for p in list(ROOT.rglob("*.pyc")):
        try:
            p.unlink()
        except FileNotFoundError:
            pass
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    pyc = list(ROOT.rglob("*.pyc"))
    caches = [p for p in ROOT.rglob("__pycache__")]
    ok = not missing and not pyc and not caches
    report = {"v23_1_to_v65_0_full_replace_gate": "pass" if ok else "fail", "missing": missing, "pyc_count": len(pyc), "cache_count": len(caches), "cache_cleanup": True}
    (ROOT / "V23_1_TO_V65_0_FULL_REPLACE_GATE.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False)); raise SystemExit(0 if ok else 1)
if __name__ == "__main__":
    main()
