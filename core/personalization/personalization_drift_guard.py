from __future__ import annotations

from typing import Dict, List
from .schemas import DriftGuardReport, DriftLevel, PreferenceStrength, new_id


class PersonalizationDriftGuard:
    """V164: prevents accidental profile/personality drift."""

    HARD_KEYS = {"risk.high_risk", "delivery.mode"}

    def evaluate_updates(self, proposed_updates: Dict[str, str], existing_strengths: Dict[str, PreferenceStrength]) -> DriftGuardReport:
        changed = list(proposed_updates)
        blocked: List[str] = []
        allowed: List[str] = []
        for key in changed:
            strength = existing_strengths.get(key, PreferenceStrength.MEDIUM)
            if key in self.HARD_KEYS and strength in {PreferenceStrength.HIGH, PreferenceStrength.HARD}:
                # allow same-direction update, block abrupt replacement
                if key == "delivery.mode" and proposed_updates[key] == "package_and_command":
                    allowed.append(key)
                else:
                    blocked.append(key)
            else:
                allowed.append(key)

        if blocked:
            level = DriftLevel.NEEDS_CONFIRMATION
            reason = "hard preference update requires confirmation"
        elif len(allowed) >= 3:
            level = DriftLevel.WATCH
            reason = "multiple preference changes detected"
        else:
            level = DriftLevel.STABLE
            reason = "safe personalization update"

        return DriftGuardReport(
            id=new_id("drift_guard"),
            level=level,
            changed_keys=changed,
            blocked_updates=blocked,
            allowed_updates=allowed,
            reason=reason,
        )
