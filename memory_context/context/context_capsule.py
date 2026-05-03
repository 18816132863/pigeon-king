"""ContextCapsule — 上下文胶囊

把启动时最重要的上下文压成固定结构，
按优先级裁剪，安全红线永不裁剪。
P0: 安全红线、当前目标、禁止动作
P1: 人格状态、关系摘要、下一步
P2: 可裁剪
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

CONTEXT_DIR = Path.cwd() / ".context_state"
CONTEXT_DIR.mkdir(parents=True, exist_ok=True)

P0_NEVER_CUT = "p0_never_cut"
P1_HIGH = "p1_high"
P2_CUTTABLE = "p2_cuttables"


@dataclass
class ContextCapsule:
    identity_summary: str = ""
    standing_orders_summary: str = ""
    current_user_profile: str = ""
    active_projects: list[dict] = field(default_factory=list)
    current_goal: str = ""
    recent_failures: list[dict] = field(default_factory=list)
    recent_successes: list[dict] = field(default_factory=list)
    active_constraints: list[str] = field(default_factory=list)
    safety_red_lines: list[str] = field(default_factory=list)
    persona_state_summary: dict = field(default_factory=dict)
    relationship_summary: dict = field(default_factory=dict)
    tool_availability_summary: dict = field(default_factory=dict)
    last_session_handoff: Optional[dict] = None
    must_not_forget: list[str] = field(default_factory=list)
    must_not_repeat: list[str] = field(default_factory=list)
    next_best_action: str = ""

    MAX_CHARS = 6000

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if not k.startswith("MAX_")}

    @classmethod
    def from_dict(cls, data: dict) -> ContextCapsule:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def estimate_chars(self) -> int:
        return len(json.dumps(self.to_dict(), ensure_ascii=False, default=str))

    def cut_to_fit(self, max_chars: int = MAX_CHARS):
        if self.estimate_chars() <= max_chars:
            return
        if len(self.recent_successes) > 2:
            self.recent_successes = self.recent_successes[-2:]
        if len(self.active_projects) > 1:
            self.active_projects = self.active_projects[-1:]
        if self.persona_state_summary:
            self.persona_state_summary = {k: v for k, v in self.persona_state_summary.items()
                                          if k in ("mood", "current_mode", "energy")}
        if self.estimate_chars() <= max_chars:
            return
        self.recent_successes = []
        self.active_projects = []
        self.tool_availability_summary = {}
        self.relationship_summary = {}
        if self.standing_orders_summary and len(self.standing_orders_summary) > 200:
            self.standing_orders_summary = self.standing_orders_summary[:197] + "..."
        if self.estimate_chars() > max_chars and len(self.identity_summary) > 300:
            self.identity_summary = self.identity_summary[:297] + "..."


class ContextCapsuleStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or CONTEXT_DIR / "context_capsule.json"

    def load(self) -> ContextCapsule | None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                return ContextCapsule.from_dict(data)
            except Exception:
                return None
        return None

    def save(self, capsule: ContextCapsule):
        capsule.cut_to_fit()
        self.path.write_text(
            json.dumps(capsule.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def build(self, **kwargs) -> ContextCapsule:
        capsule = ContextCapsule(**{k: v for k, v in kwargs.items()
                                    if k in ContextCapsule.__dataclass_fields__})
        capsule.cut_to_fit()
        self.save(capsule)
        return capsule


_capsule_store: ContextCapsuleStore | None = None


def get_context_capsule_store() -> ContextCapsuleStore:
    global _capsule_store
    if _capsule_store is None:
        _capsule_store = ContextCapsuleStore()
    return _capsule_store
