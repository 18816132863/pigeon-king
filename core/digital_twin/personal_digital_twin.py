from __future__ import annotations

from .preference_twin import PreferenceTwin
from .decision_twin import DecisionTwin
from .risk_twin import RiskTwin
from .habit_twin import HabitTwin
from .identity_drift_guard import IdentityDriftGuard


class PersonalDigitalTwin:
    """V10.8 personal digital twin: preferences, decision style, risk and habits."""

    def __init__(self) -> None:
        self.preference = PreferenceTwin()
        self.decision = DecisionTwin()
        self.risk = RiskTwin()
        self.habit = HabitTwin()
        self.guard = IdentityDriftGuard()

    def build(self, signals: list[dict] | None = None, decisions: list[dict] | None = None, feedback: list[dict] | None = None, events: list[dict] | None = None) -> dict:
        twin = {
            "preference": self.preference.infer(signals or []),
            "decision": self.decision.model(decisions or []),
            "risk": self.risk.calibrate(feedback or []),
            "habit": self.habit.extract(events or []),
        }
        guard = self.guard.check(twin)
        return {
            "status": "digital_twin_ready",
            "shape": "Personal Digital Twin",
            "twin": twin,
            "guard": guard,
            "privacy": "local_only",
        }
