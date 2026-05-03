from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import ObservabilityReport, new_id
from .storage import JsonStore


class ObservabilityReporter:
    """V115: compact operations report for the personal agent."""

    def __init__(self, root: str | Path = ".self_evolution_ops_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "observability_events.json")

    def record_event(self, event: Dict) -> None:
        self.store.append(event)

    def report(self) -> ObservabilityReport:
        events = self.store.read([])
        runs = len(events)
        successes = sum(1 for e in events if e.get("success", False))
        qualities = [float(e.get("quality", 0.0)) for e in events if "quality" in e]
        budget_violations = sum(1 for e in events if e.get("budget_violation", False))
        privacy_events = sum(1 for e in events if e.get("privacy_level") in {"sensitive", "secret"})
        open_circuits = sum(1 for e in events if e.get("circuit_status") == "open")

        success_rate = round(successes / max(1, runs), 4)
        avg_quality = round(sum(qualities) / max(1, len(qualities)), 4)
        summary = f"runs={runs}, success_rate={success_rate}, avg_quality={avg_quality}, budget_violations={budget_violations}, privacy_events={privacy_events}, open_circuits={open_circuits}"

        return ObservabilityReport(
            id=new_id("obs"),
            runs=runs,
            success_rate=success_rate,
            avg_quality=avg_quality,
            budget_violations=budget_violations,
            privacy_events=privacy_events,
            open_circuits=open_circuits,
            summary=summary,
        )
