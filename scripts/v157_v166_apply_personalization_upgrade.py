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
RESULT = ROOT / "V157_V166_PERSONALIZATION_UPGRADE_RESULT.txt"

REQUIRED = [
    "core/personalization/__init__.py",
    "core/personalization/schemas.py",
    "core/personalization/user_profile.py",
    "core/personalization/preference_rules.py",
    "core/personalization/project_memory.py",
    "core/personalization/relationship_context.py",
    "core/personalization/procedure_library.py",
    "core/personalization/decision_pattern_learner.py",
    "core/personalization/feedback_trainer.py",
    "core/personalization/personalization_drift_guard.py",
    "core/personalization/personalization_scorecard.py",
    "core/personalization/personalization_kernel.py",
    "agent_kernel/personalization.py",
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
        "V157-V166 PERSONALIZATION UPGRADE RESULT",
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
        from core.personalization import init_personalization, run_personalization_cycle
        init = init_personalization(".v157_v166_state")
        lines.append(f"Init personalization: PASS => {init}")

        cases = [
            ("upgrade", "继续推进十个大版本并给压缩包和命令", None),
            ("feedback", "继续推进版本", "不要一点点改，直接给压缩包和命令"),
            ("risk", "给客户发送邮件前先等我确认", None),
            ("commerce", "给小谷元直播运营团队出话术资料包", None),
        ]
        for label, goal, feedback in cases:
            r = run_personalization_cycle(goal, feedback_message=feedback, root=".v157_v166_state")
            lines.append(
                f"Cycle {label}: {r.status.value} | prefs={r.matched_preferences} | projects={r.matched_projects} | "
                f"rels={r.matched_relationships} | procedure={r.selected_procedure} | score={r.score}"
            )
            if not r.run_id or not r.selected_procedure or r.score <= 0:
                ok = False
                lines.append(f"Cycle check {label}: FAIL")

    except Exception as e:
        ok = False
        lines.append("Runtime verification: FAIL")
        lines.append(repr(e))

    lines.append(f"Final cache cleanup: {clean_cache()}")
    lines.append("")
    lines.append("PASS: V157-V166 personalization upgrade applied and verified." if ok else "FAIL: V157-V166 personalization upgrade has blocking issues.")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
