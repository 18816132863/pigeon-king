"""
V24.9 Device Dependency Barrier

If a device action timed out and is pending verification, dependent device actions
must not execute. Independent non-device actions may continue.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Set


BLOCKING_STATUSES = {"timeout_pending_verify", "leased_pending_verify", "unknown_result"}


@dataclass
class ActionState:
    action_id: str
    status: str
    depends_on: List[str] = field(default_factory=list)
    end_side: bool = True


class DeviceDependencyBarrier:
    def blocked_dependencies(self, action: ActionState, states: Dict[str, ActionState]) -> Set[str]:
        blocked: Set[str] = set()
        for dep_id in action.depends_on:
            dep = states.get(dep_id)
            if dep and dep.status in BLOCKING_STATUSES:
                blocked.add(dep_id)
        return blocked

    def can_execute(self, action: ActionState, states: Dict[str, ActionState]) -> bool:
        # Non-device local work can continue unless it explicitly depends on a blocked action.
        return not self.blocked_dependencies(action, states)

    def classify_next(self, actions: Iterable[ActionState], states: Dict[str, ActionState]) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for action in actions:
            blocked = self.blocked_dependencies(action, states)
            if blocked:
                result[action.action_id] = "blocked_by_pending_verify:" + ",".join(sorted(blocked))
            else:
                result[action.action_id] = "ready"
        return result
