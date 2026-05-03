"""SessionHandoff — 会话交接包

每次 compact 前、任务结束后、上下文可能丢失前，生成交接包。
用于下个会话恢复状态。

含用户真实目标、已/未完成项、卡点、验证报告、人格快照、
禁止重复事项。latest覆盖+history追加。
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

CONTEXT_DIR = Path.cwd() / ".context_state"
CONTEXT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SessionHandoff:
    user_real_goal: str = ""
    completed_items: list[str] = field(default_factory=list)
    uncompleted_items: list[str] = field(default_factory=list)
    current_blocker: str = ""
    verified_reports: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    next_continue_from: str = ""
    persona_state_snapshot: dict = field(default_factory=dict)
    user_preferences_snapshot: dict = field(default_factory=dict)
    do_not_repeat: list[str] = field(default_factory=list)
    retain_paths: list[str] = field(default_factory=list)
    session_id: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "user_real_goal": self.user_real_goal,
            "completed_items": self.completed_items,
            "uncompleted_items": self.uncompleted_items,
            "current_blocker": self.current_blocker,
            "verified_reports": self.verified_reports,
            "failures": self.failures,
            "next_continue_from": self.next_continue_from,
            "persona_state_snapshot": self.persona_state_snapshot,
            "user_preferences_snapshot": self.user_preferences_snapshot,
            "do_not_repeat": self.do_not_repeat,
            "retain_paths": self.retain_paths,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SessionHandoff:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class SessionHandoffStore:
    def __init__(self, path: Optional[Path] = None, history_path: Optional[Path] = None):
        self.path = path or CONTEXT_DIR / "session_handoff_latest.json"
        self.history_path = history_path or CONTEXT_DIR / "session_handoff_history.jsonl"

    def load_latest(self) -> SessionHandoff | None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                return SessionHandoff.from_dict(data)
            except Exception:
                return None
        return None

    def save(self, handoff: SessionHandoff):
        handoff.timestamp = datetime.now().isoformat()
        self.path.write_text(
            json.dumps(handoff.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        with open(self.history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(handoff.to_dict(), ensure_ascii=False) + "\n")

    def save_compact(self, handoff: SessionHandoff):
        """compact 专用保存——仅写 latest，不追加 history"""
        handoff.timestamp = datetime.now().isoformat()
        self.path.write_text(
            json.dumps(handoff.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_history(self, n: int = 10) -> list[SessionHandoff]:
        entries = []
        if self.history_path.exists():
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            entries.append(SessionHandoff.from_dict(data))
            except Exception:
                pass
        return entries[-n:]

    def build_and_save(self, **kwargs) -> SessionHandoff:
        import uuid
        handoff = SessionHandoff(
            session_id=str(uuid.uuid4())[:8],
            **{k: v for k, v in kwargs.items() if k in SessionHandoff.__dataclass_fields__},
        )
        self.save(handoff)
        return handoff

    def exists(self) -> bool:
        return self.path.exists()


_handoff_store: SessionHandoffStore | None = None


def get_session_handoff_store() -> SessionHandoffStore:
    global _handoff_store
    if _handoff_store is None:
        _handoff_store = SessionHandoffStore()
    return _handoff_store
