from __future__ import annotations


class RuntimeStateMachine:
    STATES = (
        "idle",
        "observing",
        "planning",
        "waiting_confirmation",
        "executing",
        "verifying",
        "learning",
        "blocked",
    )

    VALID_TRANSITIONS = {
        "idle": {"observing"},
        "observing": {"planning", "blocked"},
        "planning": {"waiting_confirmation", "executing", "blocked"},
        "waiting_confirmation": {"executing", "blocked", "idle"},
        "executing": {"verifying", "blocked"},
        "verifying": {"learning", "executing", "blocked"},
        "learning": {"idle", "observing"},
        "blocked": {"idle"},
    }

    def __init__(self) -> None:
        self.state = "idle"

    def transition(self, target: str) -> dict:
        if target not in self.STATES:
            return {"status": "rejected", "reason": "unknown_state", "state": self.state}
        if target not in self.VALID_TRANSITIONS.get(self.state, set()):
            return {"status": "rejected", "reason": "invalid_transition", "state": self.state, "target": target}
        old = self.state
        self.state = target
        return {"status": "ok", "from": old, "to": target}
