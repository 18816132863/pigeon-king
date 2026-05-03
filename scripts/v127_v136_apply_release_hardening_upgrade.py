#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
RESULT = ROOT / "V127_V136_RELEASE_HARDENING_UPGRADE_RESULT.txt"

REQUIRED = [
    "core/release_hardening/__init__.py",
    "core/release_hardening/schemas.py",
    "core/release_hardening/environment_doctor.py",
    "core/release_hardening/config_contract.py",
    "core/release_hardening/dependency_guard.py",
    "core/release_hardening/snapshot_manager.py",
    "core/release_hardening/rollback_manager.py",
    "core/release_hardening/regression_matrix.py",
    "core/release_hardening/release_manifest.py",
    "core/release_hardening/deployment_profile.py",
    "core/release_hardening/runtime_report.py",
    "core/release_hardening/release_hardening_kernel.py",
    "agent_kernel/release_hardening.py",
]


def clean_cache() -> int:
    count = 0
    for p in list(ROOT.rglob("__pycache__")) + list(ROOT.rglob(".pytest_cache")):
        try:
            shutil.rmtree(p)
            count += 1
        except Exception:
            pass
    for p in list(ROOT.rglob("*.pyc")):
        try:
            p.unlink()
            count += 1
        except Exception:
            pass
    return count


def main() -> int:
    lines = [
        "V127-V136 RELEASE HARDENING UPGRADE RESULT",
        "=" * 72,
        f"Time: {datetime.now().isoformat(timespec='seconds')}",
        f"Root: {ROOT}",
        "",
    ]
    ok = True
    lines.append(f"Cache cleaned: {clean_cache()}")

    missing = [x for x in REQUIRED if not (ROOT / x).exists()]
    if missing:
        ok = False
        lines.append("Required files: FAIL")
        lines.extend([f"  - {m}" for m in missing])
    else:
        lines.append("Required files: PASS")

    try:
        from core.release_hardening import init_release_hardening, run_release_hardening_cycle
        from core.release_hardening.schemas import ProfileName
        init = init_release_hardening(".", ".v127_v136_state")
        lines.append(f"Init release hardening: PASS => {init}")

        local = run_release_hardening_cycle("准备 V127-V136 覆盖发布", ProfileName.LOCAL, root=".", state_root=".v127_v136_state")
        lines.append(
            f"Local cycle: {local.release_status.value} | env={local.env_status.value} | "
            f"config={local.config_status.value} | dep={local.dependency_status.value} | "
            f"snapshot={local.snapshot_status.value} | regression={local.regression_status.value} | score={local.score}"
        )
        if not local.run_id or local.regression_status.value != "pass":
            ok = False
            lines.append("Local cycle check: FAIL")

        prod = run_release_hardening_cycle("准备生产发布门禁", ProfileName.PROD, root=".", state_root=".v127_v136_state")
        lines.append(
            f"Prod gate: {prod.deployment_gate.value} | status={prod.release_status.value} | next={prod.next_action}"
        )
        if prod.deployment_gate.value not in {"warn", "open", "closed"}:
            ok = False
            lines.append("Prod gate check: FAIL")

    except Exception as e:
        ok = False
        lines.append("Runtime verification: FAIL")
        lines.append(repr(e))

    lines.append(f"Final cache cleanup: {clean_cache()}")
    lines.append("")
    lines.append("PASS: V127-V136 release hardening upgrade applied and verified." if ok else "FAIL: V127-V136 release hardening upgrade has blocking issues.")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
