#!/usr/bin/env python3
from pathlib import Path
import json, shutil
ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "scripts/v23_1_to_v65_0_full_replace_gate.py",
    "scripts/v56_0_to_v65_0_all_smoke.py",
    "scripts/v66_0_to_v75_0_all_smoke.py",
    "scripts/v75_0_self_evolving_personal_os_gate.py",
    "core/mission/autonomy_horizon_planner_v7.py",
    "execution/device_conflict_resolver_v7.py",
    "agent_kernel/self_evolving_os_command_center_v7.py",
    "governance/policy/connector_governance_broker_v7.py",
    "infrastructure/skill_supply_chain_attestation_v7.py",
]
def main():
    for p in list(ROOT.rglob("__pycache__")):
        shutil.rmtree(p, ignore_errors=True)
    for p in list(ROOT.rglob("*.pyc")):
        try: p.unlink()
        except FileNotFoundError: pass
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    pyc = list(ROOT.rglob("*.pyc"))
    caches = [p for p in ROOT.rglob("__pycache__")]
    ok = not missing and not pyc and not caches
    report = {"v23_1_to_v75_0_full_replace_gate": "pass" if ok else "fail", "missing": missing, "pyc_count": len(pyc), "cache_count": len(caches)}
    (ROOT / "V23_1_TO_V75_0_FULL_REPLACE_GATE.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if ok else 1)
if __name__ == "__main__":
    main()
