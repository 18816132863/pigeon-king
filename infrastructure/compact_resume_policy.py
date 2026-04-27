"""
V23.5 Compact Resume Policy.

This extends Context Resume rules with explicit anti-stall guarantees:
- long tasks must write a state file before heavy work
- completed steps are never repeated
- pending steps are the source of truth after compaction or restart
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class CompactResumeState:
    task_id: str
    current_version: str
    current_phase: str
    completed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)
    last_output_file: str = ""
    next_command: str = ""
    resume_instruction: str = "read current_task_state.json and continue from pending_steps only"
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def mark_complete(self, step: str) -> None:
        if step not in self.completed_steps:
            self.completed_steps.append(step)
        self.pending_steps = [s for s in self.pending_steps if s != step]
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def build_resume_state(task_id: str, version: str, phase: str, pending_steps: List[str]) -> CompactResumeState:
    return CompactResumeState(
        task_id=task_id,
        current_version=version,
        current_phase=phase,
        pending_steps=list(pending_steps),
        next_command="/usr/bin/python3 scripts/resume_current_task.py",
    )
