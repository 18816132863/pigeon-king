from __future__ import annotations

from .decision_trace_index import DecisionTraceIndex
from .mistake_prevention_rules import MistakePreventionRules


class AuditReplayLearner:
    """Replay old decisions to prevent repeated mistakes."""

    def __init__(self) -> None:
        self.index = DecisionTraceIndex()
        self.rules = MistakePreventionRules()

    def learn(self, traces: list[dict]) -> dict:
        failures = []
        for t in traces:
            self.index.add(t)
            if t.get("outcome", {}).get("status") in {"failed", "timeout"}:
                failures.append(t)
        return {
            "status": "audit_replay_learned",
            "indexed": len(traces),
            "prevention_rules": self.rules.derive(failures),
        }
