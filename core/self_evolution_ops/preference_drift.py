from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import DriftReport, DriftStatus, new_id
from .storage import JsonStore


class PreferenceDriftMonitor:
    """V114: watches user preference drift and prevents personality/policy drift."""

    def __init__(self, root: str | Path = ".self_evolution_ops_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "preference_snapshots.json")

    def snapshot(self, preferences: Dict[str, str]) -> None:
        self.store.append({"preferences": preferences})

    def check(self, current_preferences: Dict[str, str]) -> DriftReport:
        snapshots = self.store.read([])
        if not snapshots:
            self.snapshot(current_preferences)
            return DriftReport(
                id=new_id("drift"),
                status=DriftStatus.STABLE,
                drift_score=0.0,
                changed_preferences=[],
                suggested_actions=["baseline created"],
            )

        previous = snapshots[-1].get("preferences", {})
        changed = []
        keys = set(previous) | set(current_preferences)
        for k in keys:
            if previous.get(k) != current_preferences.get(k):
                changed.append(k)

        drift_score = round(len(changed) / max(1, len(keys)), 4)
        if drift_score >= 0.5:
            status = DriftStatus.DRIFTING
            actions = ["ask for confirmation before rewriting long-term preference memory"]
        elif drift_score >= 0.2:
            status = DriftStatus.WATCH
            actions = ["record as tentative preference"]
        else:
            status = DriftStatus.STABLE
            actions = ["safe to update preference memory"]

        self.snapshot(current_preferences)
        return DriftReport(
            id=new_id("drift"),
            status=status,
            drift_score=drift_score,
            changed_preferences=changed,
            suggested_actions=actions,
        )
