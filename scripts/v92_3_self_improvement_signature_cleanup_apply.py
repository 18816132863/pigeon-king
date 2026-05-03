#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "core" / "self_evolution_ops" / "self_improvement_loop.py"
REPORT = ROOT / "reports" / "V92_3_SELF_IMPROVEMENT_SIGNATURE_CLEANUP_APPLY.json"
BACKUP_DIR = ROOT / ".repair_state" / ("v92_3_self_improvement_signature_cleanup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))

def _line_starts(lines, prefix):
    return [i for i, line in enumerate(lines) if line.startswith(prefix)]

def _find_block_end(lines, start_idx):
    for j in range(start_idx + 1, len(lines)):
        line = lines[j]
        if j > start_idx and (line.startswith("def ") or line.startswith("class ")):
            return j
    return len(lines)

def _ensure_goal_signature(lines, def_idx):
    old = lines[def_idx]
    indent = old[: len(old) - len(old.lstrip())]
    lines[def_idx] = f"{indent}def run_self_evolution_cycle(goal: str = None, context=None, **kwargs):\n"
    return old != lines[def_idx]

def _ensure_goal_guard(lines, def_idx):
    marker = "V92_3_GOAL_DEFAULT_GUARD"
    body_window = "".join(lines[def_idx : min(def_idx + 20, len(lines))])
    if marker in body_window:
        return False
    guard = [
        "    # V92_3_GOAL_DEFAULT_GUARD\n",
        "    if goal is None:\n",
        "        goal = 'v92_offline_self_improvement_smoke'\n",
        "    if context is None:\n",
        "        context = {}\n",
    ]
    insert_at = def_idx + 1
    if insert_at < len(lines):
        stripped = lines[insert_at].lstrip()
        if stripped.startswith(chr(34)*3) or stripped.startswith(chr(39)*3):
            quote = chr(34)*3 if stripped.startswith(chr(34)*3) else chr(39)*3
            insert_at += 1
            while insert_at < len(lines):
                if quote in lines[insert_at]:
                    insert_at += 1
                    break
                insert_at += 1
    lines[insert_at:insert_at] = guard
    return True

def main():
    os.environ.setdefault("OFFLINE_MODE", "true")
    os.environ.setdefault("NO_EXTERNAL_API", "true")
    os.environ.setdefault("NO_REAL_SEND", "true")
    os.environ.setdefault("NO_REAL_PAYMENT", "true")
    os.environ.setdefault("NO_REAL_DEVICE", "true")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "fail",
        "target": str(TARGET),
        "changes": [],
        "errors": [],
        "offline": True,
        "real_side_effects": False,
    }

    if not TARGET.exists():
        result["errors"].append("target_missing")
        REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TARGET, BACKUP_DIR / "self_improvement_loop.py.bak")

    text = TARGET.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    starts = _line_starts(lines, "def run_self_evolution_cycle(")
    result["defs_before"] = len(starts)
    if not starts:
        result["errors"].append("run_self_evolution_cycle_not_found")
        REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    if len(starts) > 1:
        for start in reversed(starts[1:]):
            end = _find_block_end(lines, start)
            del lines[start:end]
            result["changes"].append({"removed_duplicate_def_start_line": start + 1, "removed_until_line": end})
        result["changes"].append("duplicate_run_self_evolution_cycle_removed")

    starts = _line_starts(lines, "def run_self_evolution_cycle(")
    def_idx = starts[0]

    if _ensure_goal_signature(lines, def_idx):
        result["changes"].append("signature_normalized_goal_default")
    if _ensure_goal_guard(lines, def_idx):
        result["changes"].append("goal_default_guard_inserted")

    TARGET.write_text("".join(lines), encoding="utf-8")

    final = TARGET.read_text(encoding="utf-8")
    result["defs_after"] = len(re.findall(r"^def run_self_evolution_cycle\(", final, flags=re.M))
    result["has_args_signature"] = bool(re.search(r"^def run_self_evolution_cycle\(\*args", final, flags=re.M))
    result["backup_dir"] = str(BACKUP_DIR)

    if result["defs_after"] == 1 and not result["has_args_signature"]:
        result["status"] = "pass"
    else:
        result["errors"].append("post_verify_failed")

    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())
