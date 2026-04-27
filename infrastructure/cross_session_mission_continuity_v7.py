"""V73.0 Cross-session mission continuity state."""
from dataclasses import dataclass, field
from typing import List, Dict, Any
import json
from pathlib import Path

@dataclass
class ContinuityState:
    mission_id: str
    completed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)
    last_safe_checkpoint: str = "start"
    evidence_ids: List[str] = field(default_factory=list)

class MissionContinuityStore:
    layer = "L6_INFRASTRUCTURE"

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: ContinuityState) -> None:
        self.path.write_text(json.dumps(state.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> ContinuityState:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return ContinuityState(**data)

    def resume_instruction(self) -> Dict[str, Any]:
        state = self.load()
        return {"mission_id": state.mission_id, "resume_from": state.pending_steps[0] if state.pending_steps else None, "completed_steps": state.completed_steps}
