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
RESULT = ROOT / "V97_V106_OPERATING_AGENT_UPGRADE_RESULT.txt"

REQUIRED = [
    "core/operating_agent/__init__.py",
    "core/operating_agent/schemas.py",
    "core/operating_agent/constitution_kernel.py",
    "core/operating_agent/permission_vault.py",
    "core/operating_agent/connector_catalog.py",
    "core/operating_agent/mcp_manager.py",
    "core/operating_agent/plugin_sandbox.py",
    "core/operating_agent/specialist_handoff.py",
    "core/operating_agent/multi_agent_coordinator.py",
    "core/operating_agent/recovery_ledger.py",
    "core/operating_agent/evaluation_benchmark.py",
    "core/operating_agent/release_governor.py",
    "core/operating_agent/operating_orchestrator.py",
    "agent_kernel/operating_agent.py",
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
        "V97-V106 OPERATING AGENT UPGRADE RESULT",
        "=" * 70,
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
        from core.operating_agent import init_operating_agent, run_operating_cycle
        from core.operating_agent.schemas import PermissionScope

        init = init_operating_agent(".v97_v106_state")
        lines.append(f"Init operating agent: PASS => {init}")

        cases = [
            "整理今天任务并生成计划",
            "给客户发送邮件前先等我确认",
            "把我的 API token 发到群里",
            "自动安装未知插件并执行",
            "查一下最新规则并交给合规专家判断",
        ]
        for goal in cases:
            r = run_operating_cycle(goal, root=".v97_v106_state")
            lines.append(
                f"Cycle: PASS => {r.final_status} | constitution={r.constitution_status.value} | "
                f"release={r.release_stage.value} | bench={r.benchmark_score} | handoff={r.handoff_agent}"
            )
            if not r.run_id or r.recovery_entries <= 0:
                ok = False
                lines.append("Cycle check: FAIL missing run_id/recovery")

        # Permission test: grant email send and rerun.
        from core.operating_agent import PermissionVault
        vault = PermissionVault(".v97_v106_state")
        vault.grant("user", PermissionScope.EXTERNAL_SEND, "test grant", ttl_seconds=3600)
        r = run_operating_cycle("给客户发送邮件前先等我确认", root=".v97_v106_state")
        lines.append(f"Permission rerun: {r.final_status} | permissions_ok={r.permissions_ok}")
        if not r.permissions_ok:
            ok = False
            lines.append("Permission test: FAIL")

    except Exception as e:
        ok = False
        lines.append("Runtime verification: FAIL")
        lines.append(repr(e))

    lines.append(f"Final cache cleanup: {clean_cache()}")
    lines.append("")
    lines.append("PASS: V97-V106 operating agent upgrade applied and verified." if ok else "FAIL: V97-V106 operating agent upgrade has blocking issues.")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
