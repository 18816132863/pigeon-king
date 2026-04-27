"""Context resume state for long-running local agent tasks.

This module deliberately stores progress outside the chat context so a long task can
be resumed after context compaction, model restart, UI interruption, or a long
period without visible output.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_STATE_PATH = Path("task_state/current_task_state.json")
DEFAULT_EVENT_LOG = Path("task_state/context_resume_events.jsonl")


def _utc_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _now_epoch() -> float:
    return time.time()


@dataclass
class TaskState:
    task_id: str
    current_version: str
    current_phase: str
    completed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)
    last_output_file: str = ""
    next_command: str = ""
    resume_instruction: str = ""
    updated_at: str = field(default_factory=_utc_ts)
    heartbeat_at: str = field(default_factory=_utc_ts)
    heartbeat_epoch: float = field(default_factory=_now_epoch)
    status: str = "running"
    interruption_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskState":
        data = dict(data)
        data.setdefault("task_id", f"task-{uuid.uuid4().hex[:12]}")
        data.setdefault("current_version", "unknown")
        data.setdefault("current_phase", "unknown")
        data.setdefault("completed_steps", [])
        data.setdefault("pending_steps", [])
        data.setdefault("last_output_file", "")
        data.setdefault("next_command", "")
        data.setdefault("resume_instruction", "")
        data.setdefault("updated_at", _utc_ts())
        data.setdefault("heartbeat_at", data.get("updated_at", _utc_ts()))
        data.setdefault("heartbeat_epoch", _now_epoch())
        data.setdefault("status", "running")
        data.setdefault("interruption_reason", "")
        data.setdefault("metadata", {})
        return cls(**data)


class ContextResumeStore:
    """Atomic task-state store with event logging and duplicate-step protection."""

    def __init__(self, root: Optional[Path | str] = None, state_path: Optional[Path | str] = None):
        self.root = Path(root or ".").resolve()
        self.state_path = self._resolve(state_path or DEFAULT_STATE_PATH)
        self.event_log = self._resolve(DEFAULT_EVENT_LOG)

    def _resolve(self, path: Path | str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self.root / p
        return p

    def exists(self) -> bool:
        return self.state_path.exists()

    def load(self) -> Optional[TaskState]:
        if not self.state_path.exists():
            return None
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        return TaskState.from_dict(data)

    def save(self, state: TaskState, event: str = "state_saved") -> TaskState:
        state.updated_at = _utc_ts()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.state_path)
        self.append_event(event, state)
        return state

    def append_event(self, event: str, state: TaskState, extra: Optional[Dict[str, Any]] = None) -> None:
        self.event_log.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "event": event,
            "task_id": state.task_id,
            "current_version": state.current_version,
            "current_phase": state.current_phase,
            "status": state.status,
            "pending_count": len(state.pending_steps),
            "completed_count": len(state.completed_steps),
            "updated_at": _utc_ts(),
        }
        if extra:
            record["extra"] = extra
        with self.event_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def start_task(
        self,
        *,
        current_version: str,
        current_phase: str,
        pending_steps: Iterable[str],
        task_id: Optional[str] = None,
        completed_steps: Optional[Iterable[str]] = None,
        last_output_file: str = "",
        next_command: str = "",
        resume_instruction: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskState:
        state = TaskState(
            task_id=task_id or f"task-{uuid.uuid4().hex[:12]}",
            current_version=current_version,
            current_phase=current_phase,
            completed_steps=list(completed_steps or []),
            pending_steps=list(pending_steps),
            last_output_file=last_output_file,
            next_command=next_command,
            resume_instruction=resume_instruction or "读取 task_state/current_task_state.json 后，从 pending_steps 继续，不要重新分析全部聊天历史。",
            metadata=dict(metadata or {}),
        )
        return self.save(state, event="task_started")

    def heartbeat(self) -> TaskState:
        state = self.require_state()
        state.heartbeat_at = _utc_ts()
        state.heartbeat_epoch = _now_epoch()
        return self.save(state, event="heartbeat")

    def update_phase(
        self,
        current_phase: str,
        *,
        current_version: Optional[str] = None,
        next_command: Optional[str] = None,
        last_output_file: Optional[str] = None,
        pending_steps: Optional[Iterable[str]] = None,
    ) -> TaskState:
        state = self.require_state()
        state.current_phase = current_phase
        if current_version is not None:
            state.current_version = current_version
        if next_command is not None:
            state.next_command = next_command
        if last_output_file is not None:
            state.last_output_file = last_output_file
        if pending_steps is not None:
            state.pending_steps = list(pending_steps)
        return self.save(state, event="phase_updated")

    def complete_step(self, step: str, *, last_output_file: Optional[str] = None) -> TaskState:
        state = self.require_state()
        if step in state.pending_steps:
            state.pending_steps.remove(step)
        if step not in state.completed_steps:
            state.completed_steps.append(step)
        if last_output_file is not None:
            state.last_output_file = last_output_file
        if not state.pending_steps and state.status != "interrupted":
            state.status = "completed"
        return self.save(state, event="step_completed")

    def mark_interrupted(self, reason: str = "context_compacted_or_response_interrupted") -> TaskState:
        state = self.require_state()
        state.status = "interrupted"
        state.interruption_reason = reason
        return self.save(state, event="task_interrupted")

    def mark_running(self) -> TaskState:
        state = self.require_state()
        state.status = "running"
        state.interruption_reason = ""
        return self.save(state, event="task_resumed")

    def mark_completed(self) -> TaskState:
        state = self.require_state()
        state.status = "completed"
        state.pending_steps = []
        return self.save(state, event="task_completed")

    def require_state(self) -> TaskState:
        state = self.load()
        if state is None:
            raise FileNotFoundError(f"missing context resume state: {self.state_path}")
        return state

    def should_resume(self, *, stale_after_seconds: int = 180) -> bool:
        state = self.load()
        if state is None:
            return False
        if state.status in {"interrupted", "running", "queued"} and state.pending_steps:
            return True
        if state.status == "running" and (_now_epoch() - float(state.heartbeat_epoch or 0)) >= stale_after_seconds:
            return True
        return False

    def resume_payload(self) -> Dict[str, Any]:
        state = self.require_state()
        return {
            "should_resume": self.should_resume(),
            "task_id": state.task_id,
            "current_version": state.current_version,
            "current_phase": state.current_phase,
            "status": state.status,
            "interruption_reason": state.interruption_reason,
            "completed_steps": state.completed_steps,
            "pending_steps": state.pending_steps,
            "last_output_file": state.last_output_file,
            "next_command": state.next_command,
            "resume_instruction": state.resume_instruction,
            "updated_at": state.updated_at,
            "heartbeat_at": state.heartbeat_at,
        }

    def resume_text(self) -> str:
        payload = self.resume_payload()
        pending = payload["pending_steps"]
        completed = payload["completed_steps"]
        lines = [
            "Context Resume State",
            f"task_id: {payload['task_id']}",
            f"version: {payload['current_version']}",
            f"phase: {payload['current_phase']}",
            f"status: {payload['status']}",
            f"completed_steps: {len(completed)}",
            f"pending_steps: {len(pending)}",
        ]
        if payload["last_output_file"]:
            lines.append(f"last_output_file: {payload['last_output_file']}")
        if payload["next_command"]:
            lines.append(f"next_command: {payload['next_command']}")
        lines.append("resume_instruction: " + payload["resume_instruction"])
        if pending:
            lines.append("next_pending_step: " + pending[0])
        return "\n".join(lines)


__all__ = ["ContextResumeStore", "TaskState", "DEFAULT_STATE_PATH", "DEFAULT_EVENT_LOG"]
