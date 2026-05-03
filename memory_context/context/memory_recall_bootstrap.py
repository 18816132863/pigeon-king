"""MemoryRecallBootstrap — 启动记忆召回器

每次新会话/刷新后自动召回关键上下文。
只读本地文件，不调用外部 API。
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

PERSONA_DIR = Path.cwd() / ".memory_persona"
CONTEXT_DIR = Path.cwd() / ".context_state"
REPORTS_DIR = Path.cwd() / "reports"


@dataclass
class MemoryBootstrapResult:
    user_identity: str = ""
    current_projects: list[str] = field(default_factory=list)
    recent_tasks: list[str] = field(default_factory=list)
    recent_failures: list[str] = field(default_factory=list)
    recent_successes: list[str] = field(default_factory=list)
    user_style_preference: str = ""
    forbidden_items: list[str] = field(default_factory=list)
    next_step: str = ""
    sources_loaded: list[str] = field(default_factory=list)
    handoff_found: bool = False
    capsule_found: bool = False

    def to_dict(self) -> dict:
        return {
            "user_identity": self.user_identity,
            "current_projects": self.current_projects,
            "recent_tasks": self.recent_tasks,
            "recent_failures": self.recent_failures,
            "recent_successes": self.recent_successes,
            "user_style_preference": self.user_style_preference,
            "forbidden_items": self.forbidden_items,
            "next_step": self.next_step,
            "sources_loaded": self.sources_loaded,
            "handoff_found": self.handoff_found,
            "capsule_found": self.capsule_found,
        }


class MemoryRecallBootstrap:
    """启动记忆召回器"""

    def __init__(self):
        self.sources_loaded: list[str] = []

    def recall(self) -> MemoryBootstrapResult:
        result = MemoryBootstrapResult()

        # 1. SessionHandoff
        handoff_path = CONTEXT_DIR / "session_handoff_latest.json"
        if handoff_path.exists():
            try:
                data = json.loads(handoff_path.read_text(encoding="utf-8"))
                result.recent_tasks = data.get("completed_items", []) + data.get("uncompleted_items", [])
                result.recent_failures = data.get("failures", [])
                result.next_step = data.get("next_continue_from", "")
                result.handoff_found = True
                self.sources_loaded.append("session_handoff")
            except Exception:
                pass

        # 2. ContextCapsule
        capsule_path = CONTEXT_DIR / "context_capsule.json"
        if capsule_path.exists():
            try:
                data = json.loads(capsule_path.read_text(encoding="utf-8"))
                goal = data.get("current_goal", "")
                if goal and not result.next_step:
                    result.next_step = goal
                result.forbidden_items = data.get("safety_red_lines", []) + data.get("must_not_repeat", [])
                result.capsule_found = True
                self.sources_loaded.append("context_capsule")
            except Exception:
                pass

        # 3. PersonaState
        state_path = PERSONA_DIR / "persona_state.json"
        if state_path.exists():
            self.sources_loaded.append("persona_state")

        # 4. RelationshipMemory
        rel_path = PERSONA_DIR / "relationship_memory.json"
        if rel_path.exists():
            try:
                data = json.loads(rel_path.read_text(encoding="utf-8"))
                goals = data.get("user_long_term_goals", [])
                if goals and not result.current_projects:
                    result.current_projects = goals[:3]
                dislikes = data.get("user_dislikes", [])
                if dislikes:
                    result.user_style_preference = f"Avoid: {', '.join(dislikes[:3])}"
                self.sources_loaded.append("relationship_memory")
            except Exception:
                pass

        # 5. IDENTITY.md
        identity_path = Path.cwd() / "IDENTITY.md"
        if identity_path.exists():
            try:
                text = identity_path.read_text(encoding="utf-8", errors="ignore")
                result.user_identity = text[:300].replace("\n", " ").strip()
                self.sources_loaded.append("IDENTITY.md")
            except Exception:
                pass

        # 6. Recent reports
        if REPORTS_DIR.exists():
            try:
                reports = list(REPORTS_DIR.glob("*.json"))
                recent = sorted(reports, key=lambda p: p.stat().st_mtime, reverse=True)[:5]
                for r in recent:
                    self.sources_loaded.append(str(r.name))
            except Exception:
                pass

        result.sources_loaded = self.sources_loaded
        return result


_recall_bootstrap: MemoryRecallBootstrap | None = None


def get_memory_recall_bootstrap() -> MemoryRecallBootstrap:
    global _recall_bootstrap
    if _recall_bootstrap is None:
        _recall_bootstrap = MemoryRecallBootstrap()
    return _recall_bootstrap
