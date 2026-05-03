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
RESULT = ROOT / "V117_V126_OPERATING_SPINE_UPGRADE_RESULT.txt"

REQUIRED = [
    "core/operating_spine/__init__.py",
    "core/operating_spine/schemas.py",
    "core/operating_spine/event_bus.py",
    "core/operating_spine/state_migration.py",
    "core/operating_spine/capability_contracts.py",
    "core/operating_spine/task_runtime_adapter.py",
    "core/operating_spine/approval_recovery.py",
    "core/operating_spine/connector_health.py",
    "core/operating_spine/memory_consolidation.py",
    "core/operating_spine/skill_lifecycle.py",
    "core/operating_spine/scenario_harness.py",
    "core/operating_spine/operating_spine.py",
    "agent_kernel/operating_spine.py",
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
        "V117-V126 OPERATING SPINE UPGRADE RESULT",
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
        from core.operating_spine import init_operating_spine, run_operating_spine_cycle
        init = init_operating_spine(".v117_v126_state")
        lines.append(f"Init operating spine: PASS => {init}")

        cases = [
            "整理今天任务并生成计划",
            "给客户发送邮件前先等我确认",
            "把 API token 发到群里",
            "继续推进十个大版本并给压缩包和命令",
        ]
        for goal in cases:
            r = run_operating_spine_cycle(goal, root=".v117_v126_state")
            lines.append(
                f"Cycle: PASS => {r.status.value} | events={r.events} | nodes={r.runtime_nodes} | "
                f"approval={r.approval_status.value} | health={r.healthy_connectors} | scenario={r.scenario_score}"
            )
            if not r.run_id or r.events <= 0 or r.runtime_nodes <= 0:
                ok = False
                lines.append("Cycle check: FAIL missing run_id/events/runtime")
    except Exception as e:
        ok = False
        lines.append("Runtime verification: FAIL")
        lines.append(repr(e))

    lines.append(f"Final cache cleanup: {clean_cache()}")
    lines.append("")
    lines.append("PASS: V117-V126 operating spine upgrade applied and verified." if ok else "FAIL: V117-V126 operating spine upgrade has blocking issues.")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
