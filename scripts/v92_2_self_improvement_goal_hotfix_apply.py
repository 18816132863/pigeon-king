#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V92.2 hotfix: make run_self_evolution_cycle(context=...) compatible.

Fixes: TypeError: run_self_evolution_cycle() missing 1 required positional argument: 'goal'
Policy: offline only, no external API, no real side effects.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)
TARGET = ROOT / "core" / "self_evolution_ops" / "self_improvement_loop.py"
BACKUP_DIR = ROOT / ".repair_state" / "v92_2_self_improvement_goal_hotfix"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
REPORT = REPORTS / "V92_2_SELF_IMPROVEMENT_GOAL_HOTFIX_APPLY.json"

SAFE_ENV = {
    "OFFLINE_MODE": "true",
    "NO_EXTERNAL_API": "true",
    "NO_REAL_SEND": "true",
    "NO_REAL_PAYMENT": "true",
    "NO_REAL_DEVICE": "true",
}
for k, v in SAFE_ENV.items():
    os.environ.setdefault(k, v)

MARKER = "V92_2_SELF_IMPROVEMENT_GOAL_DEFAULT"

def write_report(status: str, details: dict) -> None:
    payload = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "target": str(TARGET),
        "offline_env": {k: os.environ.get(k) for k in SAFE_ENV},
        **details,
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def find_def_span(src: str):
    # Supports normal and async def, multiline signatures are uncommon but handled by scanning to ':'
    m = re.search(r"(?m)^(?P<indent>\s*)(?P<async>async\s+)?def\s+run_self_evolution_cycle\s*\(", src)
    if not m:
        return None
    start = m.start()
    i = m.end()
    depth = 1
    in_str = None
    esc = False
    while i < len(src):
        ch = src[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
        else:
            if ch in ('"', "'"):
                in_str = ch
            elif ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    # Move to end of def line/colon including return annotation
                    j = i + 1
                    while j < len(src) and src[j] != ':':
                        j += 1
                    if j < len(src):
                        line_end = src.find('\n', j)
                        if line_end == -1:
                            line_end = len(src)
                        return m, start, line_end
                    break
        i += 1
    return None


def patch_source(src: str) -> tuple[str, list[str]]:
    changes = []
    if MARKER in src:
        return src, ["already_patched"]

    span = find_def_span(src)
    if span is None:
        raise RuntimeError("run_self_evolution_cycle definition not found")
    m, start, def_line_end = span
    def_block = src[start:def_line_end]

    # Make required goal optional. Handles: goal, / goal: str, / goal: Optional[str], etc.
    patched_def = def_block
    # Replace only the first 'goal' parameter that has no default.
    # Cases: (goal, context=None), (goal: str, context=None), (goal: str | None, context=None)
    if re.search(r"\bgoal\s*=", patched_def):
        changes.append("goal_already_has_default")
    else:
        patched_def_new = re.sub(
            r"\bgoal\b(\s*:\s*[^,\)]+)?(\s*)([,\)])",
            lambda mm: f"goal{mm.group(1) or ''} = None{mm.group(3)}",
            patched_def,
            count=1,
        )
        if patched_def_new == patched_def:
            raise RuntimeError("found function but could not patch goal parameter")
        patched_def = patched_def_new
        changes.append("goal_default_added")

    indent = m.group("indent")
    body_indent = indent + "    "
    guard = (
        f"\n{body_indent}# {MARKER}: allow legacy gate call run_self_evolution_cycle(context={{...}})\n"
        f"{body_indent}if goal is None:\n"
        f"{body_indent}    if isinstance(context, dict):\n"
        f"{body_indent}        goal = (context.get('goal') or context.get('objective') or "
        f"context.get('task') or context.get('query') or 'v92_self_improvement_offline_dry_run')\n"
        f"{body_indent}    else:\n"
        f"{body_indent}        goal = 'v92_self_improvement_offline_dry_run'\n"
    )

    new_src = src[:start] + patched_def + guard + src[def_line_end:]
    changes.append("goal_guard_inserted")
    return new_src, changes


def main() -> None:
    if not TARGET.exists():
        write_report("fail", {"error": "target_missing", "remaining_failures": ["target_missing"]})
        raise SystemExit(1)

    src = TARGET.read_text(encoding="utf-8")
    backup = BACKUP_DIR / f"self_improvement_loop.py.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.bak"
    shutil.copy2(TARGET, backup)
    try:
        new_src, changes = patch_source(src)
        TARGET.write_text(new_src, encoding="utf-8")
        write_report("pass", {"changes": changes, "backup": str(backup), "remaining_failures": []})
    except Exception as e:
        shutil.copy2(backup, TARGET)
        write_report("fail", {"error": str(e), "backup_restored": str(backup), "remaining_failures": [str(e)]})
        raise SystemExit(1)

if __name__ == "__main__":
    main()
