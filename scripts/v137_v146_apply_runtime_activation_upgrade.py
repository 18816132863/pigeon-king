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
RESULT = ROOT / "V137_V146_RUNTIME_ACTIVATION_UPGRADE_RESULT.txt"

REQUIRED = [
    "core/runtime_activation/__init__.py",
    "core/runtime_activation/schemas.py",
    "core/runtime_activation/command_bus.py",
    "core/runtime_activation/api_facade.py",
    "core/runtime_activation/job_queue.py",
    "core/runtime_activation/scheduler_bridge.py",
    "core/runtime_activation/state_inspector.py",
    "core/runtime_activation/diagnostic_engine.py",
    "core/runtime_activation/policy_simulator.py",
    "core/runtime_activation/artifact_packager.py",
    "core/runtime_activation/compatibility_shim.py",
    "core/runtime_activation/runtime_activation_kernel.py",
    "agent_kernel/runtime_activation.py",
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
        "V137-V146 RUNTIME ACTIVATION UPGRADE RESULT",
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
        from core.runtime_activation import init_runtime_activation, run_runtime_activation_cycle
        init = init_runtime_activation(".", ".v137_v146_state")
        lines.append(f"Init runtime activation: PASS => {init}")

        cases = [
            "继续推进十个大版本并给压缩包和命令",
            "给客户发送邮件前先等我确认",
            "把 API token 发到群里",
            "运行当前系统状态诊断",
        ]
        for goal in cases:
            r = run_runtime_activation_cycle(goal, root=".", state_root=".v137_v146_state")
            lines.append(
                f"Cycle: {r.activation_status.value} | command={r.command_status.value} | "
                f"job={r.job_status.value} | schedule={r.schedule_status.value} | "
                f"compat={r.compatibility_status.value} | score={r.score}"
            )
            if not r.run_id or r.api_status_code != 200:
                ok = False
                lines.append("Cycle check: FAIL")
    except Exception as e:
        ok = False
        lines.append("Runtime verification: FAIL")
        lines.append(repr(e))

    lines.append(f"Final cache cleanup: {clean_cache()}")
    lines.append("")
    lines.append("PASS: V137-V146 runtime activation upgrade applied and verified." if ok else "FAIL: V137-V146 runtime activation upgrade has blocking issues.")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
