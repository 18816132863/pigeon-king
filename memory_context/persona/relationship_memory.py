"""RelationshipMemory — 关系记忆

记录用户长期偏好、交互模式、关键事件，
以持久化 JSON 文件存储。

Note: trust_level/closeness 等是 AI 内部关系状态标签，
用于调整交互策略，不代表真实人际关系。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

PERSONA_DIR = Path.cwd() / ".memory_persona"
PERSONA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class KeyEvent:
    event_type: str  # correction/praise/task_success/task_failure/milestone
    description: str
    timestamp: str = ""
    context: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> KeyEvent:
        return cls(**data)


@dataclass
class RelationshipMemory:
    user_long_term_goals: list[str] = field(default_factory=list)
    user_dislikes: list[str] = field(default_factory=list)
    user_preferred_style: list[str] = field(default_factory=list)
    user_frequent_topics: list[str] = field(default_factory=list)
    user_risk_preference: str = "conservative"
    user_persona_expectations: list[str] = field(default_factory=list)
    last_key_event: Optional[dict] = None
    last_failure_or_fix: Optional[dict] = None
    user_common_phrases: list[str] = field(default_factory=list)
    user_do_not_repeat: list[str] = field(default_factory=list)
    key_events: list[dict] = field(default_factory=list)
    interaction_count: int = 0
    correction_count: int = 0
    praise_count: int = 0
    last_updated_at: str = ""
    first_met_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> RelationshipMemory:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class RelationshipMemoryStore:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or PERSONA_DIR / "relationship_memory.json"
        self._memory: RelationshipMemory = self._load()

    def _load(self) -> RelationshipMemory:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                return RelationshipMemory.from_dict(data)
            except Exception:
                pass
        rm = RelationshipMemory()
        rm.first_met_at = datetime.now().isoformat()
        return rm

    def _save(self):
        self._memory.last_updated_at = datetime.now().isoformat()
        self.storage_path.write_text(
            json.dumps(self._memory.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @property
    def memory(self) -> RelationshipMemory:
        return self._memory

    def get_summary(self) -> dict:
        m = self._memory
        return {
            "interaction_count": m.interaction_count,
            "user_risk_preference": m.user_risk_preference,
            "last_key_event": m.last_key_event,
            "last_failure": m.last_failure_or_fix,
            "user_dislikes_count": len(m.user_dislikes),
            "user_do_not_repeat_count": len(m.user_do_not_repeat),
            "user_long_term_goals": m.user_long_term_goals[:3],
            "user_preferred_style": m.user_preferred_style[:3],
            "user_frequent_topics": m.user_frequent_topics[:5],
            "user_persona_expectations": m.user_persona_expectations[:3],
            "user_common_phrases": m.user_common_phrases[:3],
        }

    def record_interaction(self):
        self._memory.interaction_count += 1
        self._save()

    def record_correction(self, description: str, context: str = ""):
        self._memory.correction_count += 1
        event = KeyEvent(event_type="correction", description=description,
                         timestamp=datetime.now().isoformat(), context=context)
        self._memory.key_events.append(event.to_dict())
        self._memory.last_key_event = event.to_dict()
        if len(self._memory.key_events) > 100:
            self._memory.key_events = self._memory.key_events[-50:]
        self._save()

    def record_praise(self, description: str):
        self._memory.praise_count += 1
        event = KeyEvent(event_type="praise", description=description,
                         timestamp=datetime.now().isoformat())
        self._memory.key_events.append(event.to_dict())
        self._memory.last_key_event = event.to_dict()
        if len(self._memory.key_events) > 100:
            self._memory.key_events = self._memory.key_events[-50:]
        self._save()

    def record_failure(self, description: str, fix: str = ""):
        event = KeyEvent(event_type="task_failure", description=description,
                         timestamp=datetime.now().isoformat(), context=fix)
        self._memory.key_events.append(event.to_dict())
        self._memory.last_failure_or_fix = {"failure": description, "fix": fix,
                                            "timestamp": datetime.now().isoformat()}
        if len(self._memory.key_events) > 100:
            self._memory.key_events = self._memory.key_events[-50:]
        self._save()

    def add_dislike(self, item: str):
        if item not in self._memory.user_dislikes:
            self._memory.user_dislikes.append(item)
            self._save()

    def add_do_not_repeat(self, item: str):
        if item not in self._memory.user_do_not_repeat:
            self._memory.user_do_not_repeat.append(item)
            self._save()

    def add_goal(self, goal: str):
        if goal not in self._memory.user_long_term_goals:
            self._memory.user_long_term_goals.append(goal)
            self._save()

    def to_dict(self) -> dict:
        return self._memory.to_dict()


_relationship_store: Optional[RelationshipMemoryStore] = None


def get_relationship_memory() -> RelationshipMemoryStore:
    global _relationship_store
    if _relationship_store is None:
        _relationship_store = RelationshipMemoryStore()
    return _relationship_store
