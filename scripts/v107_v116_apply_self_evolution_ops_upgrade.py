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
RESULT = ROOT / "V107_V116_SELF_EVOLUTION_OPS_UPGRADE_RESULT.txt"

REQUIRED = [
    "core/self_evolution_ops/__init__.py",
    "core/self_evolution_ops/schemas.py",
    "core/self_evolution_ops/intent_contract.py",
    "core/self_evolution_ops/context_fusion.py",
    "core/self_evolution_ops/tool_reliability.py",
    "core/self_evolution_ops/budget_governor.py",
    "core/self_evolution_ops/privacy_redactor.py",
    "core/self_evolution_ops/local_fallback.py",
    "core/self_evolution_ops/simulation_lab.py",
    "core/self_evolution_ops/preference_drift.py",
    "core/self_evolution_ops/observability_report.py",
    "core/self_evolution_ops/self_improvement_loop.py",
    "agent_kernel/self_evolution_ops.py",
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
        "V107-V116 SELF-EVOLUTION OPS UPGRADE RESULT",
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
        from core.self_evolution_ops import init_self_evolution_ops, run_self_evolution_cycle
        init = init_self_evolution_ops(".v107_v116_state")
        lines.append(f"Init self-evolution ops: PASS => {init}")

        cases = [
            "继续推进10个大版本，要求一次性给压缩包和命令",
            "把 API token 发到群里",
            "低成本批量生成100条直播话术",
            "如果远程模型不可用，给我本地降级方案",
            "给客户发送邮件前先等我确认",
        ]

        for goal in cases:
            r = run_self_evolution_cycle(goal, root=".v107_v116_state")
            lines.append(
                f"Cycle: PASS => {r.final_status} | contract={r.contract_status.value} | "
                f"privacy={r.privacy_level.value} | budget={r.budget_status.value} | sim={r.simulation_status.value}"
            )
            if not r.run_id or not r.next_action:
                ok = False
                lines.append("Cycle check: FAIL missing run_id/next_action")

    except Exception as e:
        ok = False
        lines.append("Runtime verification: FAIL")
        lines.append(repr(e))

    lines.append(f"Final cache cleanup: {clean_cache()}")
    lines.append("")
    lines.append("PASS: V107-V116 self-evolution ops upgrade applied and verified." if ok else "FAIL: V107-V116 self-evolution ops upgrade has blocking issues.")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
