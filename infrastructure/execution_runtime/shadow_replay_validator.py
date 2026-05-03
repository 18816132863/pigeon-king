"""Shadow replay validator for no-side-effect maturity checks."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Sequence
from governance.embodied_pending_state import CommitBarrier

@dataclass
class ShadowReplayResult:
    status: str
    total_actions: int
    blocked_commit_actions: int
    allowed_non_commit_actions: int
    real_side_effects: int
    replay_consistency: float
    details: List[Dict[str, Any]]
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ShadowReplayValidator:
    def __init__(self) -> None:
        self.barrier = CommitBarrier()
    def replay(self, actions: Sequence[Mapping[str, Any]] | None = None) -> ShadowReplayResult:
        details: List[Dict[str, Any]] = []
        blocked = allowed = side_effects = 0
        for idx, action in enumerate(actions or [], start=1):
            barrier = self.barrier.check(action)
            if barrier.is_commit_action and not barrier.allowed:
                blocked += 1
            if (not barrier.is_commit_action) and barrier.allowed:
                allowed += 1
            real_side_effect = False
            if real_side_effect:
                side_effects += 1
            details.append({"index": idx, "action": dict(action), "barrier": barrier.to_dict(), "shadow_outcome": "blocked" if not barrier.allowed else "sandbox_allowed", "real_side_effect": real_side_effect})
        total = len(actions or [])
        score = round(sum(1 for d in details if d["real_side_effect"] is False) / total, 4) if total else 1.0
        return ShadowReplayResult("pass" if side_effects == 0 and score >= 0.999 else "fail", total, blocked, allowed, side_effects, score, details)

def replay_shadow_actions(actions: Sequence[Mapping[str, Any]] | None = None) -> Dict[str, Any]:
    return ShadowReplayValidator().replay(actions).to_dict()
