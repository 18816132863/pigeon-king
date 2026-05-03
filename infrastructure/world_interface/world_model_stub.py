"""Minimal world-model/digital-twin stub for pending-access verification."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping


@dataclass
class WorldModelState:
    state_id: str
    observations: List[Dict[str, Any]] = field(default_factory=list)
    simulated_events: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PendingWorldModel:
    def __init__(self, state_id: str = "pending_access_world") -> None:
        self.state = WorldModelState(state_id=state_id)

    def observe(self, observation: Mapping[str, Any]) -> Dict[str, Any]:
        event = {"type": "observation", "data": dict(observation), "at": datetime.now(timezone.utc).isoformat()}
        self.state.observations.append(event)
        return {"status": "observed", "event": event, "state": self.state.to_dict()}

    def simulate(self, action: Mapping[str, Any]) -> Dict[str, Any]:
        event = {
            "type": "simulation",
            "action": dict(action),
            "real_side_effect": False,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self.state.simulated_events.append(event)
        return {"status": "simulated", "event": event, "state": self.state.to_dict()}
