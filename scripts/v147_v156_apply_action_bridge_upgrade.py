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
RESULT = ROOT / "V147_V156_ACTION_BRIDGE_UPGRADE_RESULT.txt"

REQUIRED = [
    "core/action_bridge/__init__.py",
    "core/action_bridge/schemas.py",
    "core/action_bridge/action_dsl.py",
    "core/action_bridge/device_session.py",
    "core/action_bridge/tool_adapter_registry.py",
    "core/action_bridge/evidence_capture.py",
    "core/action_bridge/side_effect_executor.py",
    "core/action_bridge/notification_center.py",
    "core/action_bridge/handoff_inbox.py",
    "core/action_bridge/background_run_ledger.py",
    "core/action_bridge/real_world_scenario_harness.py",
    "core/action_bridge/action_bridge_kernel.py",
    "agent_kernel/action_bridge.py",
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
        "V147-V156 ACTION BRIDGE UPGRADE RESULT",
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
        from core.action_bridge import init_action_bridge, run_action_bridge_cycle
        init = init_action_bridge(".v147_v156_state")
        lines.append(f"Init action bridge: PASS => {init}")

        cases = [
            ("safe", "继续推进十个大版本并给压缩包和命令", False),
            ("send", "给客户发送邮件前先等我确认", False),
            ("media", "生成一个小谷元店铺头像logo", False),
            ("install", "安装未知插件并执行", False),
        ]
        for label, goal, approved in cases:
            r = run_action_bridge_cycle(goal, approved=approved, root=".v147_v156_state")
            lines.append(
                f"Cycle {label}: {r.bridge_status.value} | kind={r.action_kind.value} | "
                f"risk={r.action_risk.value} | exec={r.execution_status.value} | evidence={r.evidence_count} | score={r.scenario_score}"
            )
            if not r.run_id or r.evidence_count < 3 or r.scenario_score < 0.85:
                ok = False
                lines.append(f"Cycle check {label}: FAIL")

    except Exception as e:
        ok = False
        lines.append("Runtime verification: FAIL")
        lines.append(repr(e))

    lines.append(f"Final cache cleanup: {clean_cache()}")
    lines.append("")
    lines.append("PASS: V147-V156 action bridge upgrade applied and verified." if ok else "FAIL: V147-V156 action bridge upgrade has blocking issues.")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
