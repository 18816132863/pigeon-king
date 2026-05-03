"""V104.3 Skill Policy Gate.

Classifies skills and blocks external/send actions at runtime when offline flags are enabled.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

EXTERNAL_TOKENS = ("requests", "httpx", "urllib", "openai", "anthropic", "dashscope", "webhook", "feishu", "email", "calendar", "upload", "crawler", "tts", "music", "image generation")
SEND_TOKENS = ("send", "email", "webhook", "feishu", "push", "publish", "upload", "发送", "发布", "上传")


def offline() -> bool:
    return os.environ.get("NO_EXTERNAL_API") == "true" or os.environ.get("OFFLINE_MODE") == "true"


def classify_text(text: str) -> str:
    t = (text or "").lower()
    if any(tok in t for tok in SEND_TOKENS):
        return "approval_required" if os.environ.get("NO_REAL_SEND") != "true" else "external_api_blocked"
    if any(tok in t for tok in EXTERNAL_TOKENS):
        return "external_api_blocked" if offline() else "approval_required"
    return "offline_safe"


def classify_skill_file(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    text = ""
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")[:20000]
    except Exception:
        pass
    category = classify_text(str(p) + "\n" + text)
    return {
        "path": str(p),
        "category": category,
        "offline_allowed": category in ("offline_safe", "mock_only"),
        "requires_approval": category == "approval_required",
        "blocked_in_offline": category == "external_api_blocked",
    }


def check_action(skill: str = "", action: str = "") -> Dict[str, Any]:
    category = classify_text(f"{skill} {action}")
    blocked = category == "external_api_blocked" or (os.environ.get("NO_REAL_SEND") == "true" and any(tok in (action or '').lower() for tok in SEND_TOKENS))
    return {
        "status": "blocked" if blocked else "ok",
        "skill": skill,
        "action": action,
        "category": category,
        "side_effects": False,
        "requires_api": False,
        "no_external_api": os.environ.get("NO_EXTERNAL_API") == "true",
        "no_real_send": os.environ.get("NO_REAL_SEND") == "true",
    }


def generate_report(limit: int = 500) -> Dict[str, Any]:
    items = []
    skills_root = ROOT / "skills"
    if skills_root.exists():
        for p in list(skills_root.rglob("SKILL.md"))[:limit]:
            items.append(classify_skill_file(p))
    report = {
        "version": "V104.3",
        "status": "pass",
        "total_scanned": len(items),
        "offline_safe": len([x for x in items if x["category"] == "offline_safe"]),
        "approval_required": len([x for x in items if x["category"] == "approval_required"]),
        "external_api_blocked": len([x for x in items if x["category"] == "external_api_blocked"]),
        "items": items,
    }
    (REPORTS / "V104_3_SKILL_POLICY_ENFORCEMENT_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
