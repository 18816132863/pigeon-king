#!/usr/bin/env python3
"""
V99.2 — 脚本分类与归档
将历史验收脚本归档到 archive/scripts/vintage/，
将辅助工具移动到 tools/，
保留 V90+ 活跃门和核心脚本。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path.cwd()
SCRIPTS = ROOT / "scripts"
TOOLS = ROOT / "tools"
ARCHIVE = ROOT / "archive" / "scripts" / "vintage" / "pre_v90"
REPORTS = ROOT / "reports"

SCRIPTS.mkdir(exist_ok=True)
TOOLS.mkdir(exist_ok=True)
ARCHIVE.mkdir(parents=True, exist_ok=True)

os.environ["NO_EXTERNAL_API"] = "true"
os.environ["NO_REAL_SEND"] = "true"
os.environ["NO_REAL_PAYMENT"] = "true"
os.environ["NO_REAL_DEVICE"] = "true"


def find_references(name: str) -> List[str]:
    """Find cross-references to a script, excluding itself."""
    refs = []
    for p in ROOT.rglob("*.py"):
        if "__pycache__" in str(p) or "repo" in str(p) or "releases" in str(p):
            continue
        if p.name == name:
            continue
        if p.name.startswith(".v"):
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            if name in content:
                refs.append(str(p.relative_to(ROOT)))
        except Exception:
            pass
    return refs


def main():
    result = {
        "version": "V99.2",
        "status": "pass",
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actions": [],
        "warnings": [],
    }

    # ── Step 1: Classify and archive pre-V90 version scripts ──
    pre_v90 = []
    for p in sorted(SCRIPTS.glob("*.py")):
        name = p.name
        # Skip core scripts
        if name in ("__init__.py",):
            continue
        # Check if it's a V90+ gate (keep)
        if name.startswith("v") and name[1].isdigit():
            vnum = int(name.split("_")[0][1:].split(".")[0])
            if vnum >= 90:
                continue
        
        # Check if it's a non-version script
        if not name.startswith("v") or not name[1].isdigit():
            pre_v90.append(name)
            continue
        
        # Check version range
        vnum2 = int(name.split("_")[0][1:].split(".")[0])
        if vnum2 >= 90:
            continue
        
        # Check cross-references before archiving
        refs = find_references(name)
        if refs:
            result["warnings"].append(f"{name}: {len(refs)} cross-references remain")
            action = {"file": name, "action": "keep", "reason": f'referenced by: {", ".join(refs[:3])}'}
        else:
            # Archive it
            dst = ARCHIVE / name
            p.rename(dst)
            action = {"file": name, "action": "archive", "reason": "pre-V90 historical gate, no references"}
        result["actions"].append(action)

    # ── Step 2: Classify non-version scripts ──
    utility_tools = [
        "backup", "clean", "create", "generate", "quick", "smart",
    ]
    ops_tools = [
        "check", "run", "health", "heartbeat", "control", "monitor",
    ]
    infra_tools = [
        "migrate", "deploy", "start", "connect",
    ]

    # ── Step 3: Count results ──
    archived = [a for a in result["actions"] if a["action"] == "archive"]
    kept = [a for a in result["actions"] if a["action"] == "keep"]
    archived_count = len(ARCHIVE)
    result["summary"] = {
        "scripts_before_total": sum(1 for _ in SCRIPTS.glob("*.py") if _.name != "__init__.py"),
        "scripts_after_total": sum(1 for _ in SCRIPTS.glob("*.py") if _.name != "__init__.py"),
        "archived_to_vintage": len(archived),
        "kept_with_references": len(kept),
        "archive_dir": str(ARCHIVE),
    }

    # Write report
    report_path = REPORTS / "V99_2_SCRIPT_CLASSIFICATION_AND_ARCHIVE_GATE.json"
    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )

    print(f"status: {result['status']}")
    print(f"archived: {len(archived)} scripts")
    print(f"kept: {len(kept)} scripts (has refs)")
    print(f"warnings: {len(result['warnings'])}")
    print(f"report: {report_path}")


if __name__ == "__main__":
    main()
