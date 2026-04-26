from __future__ import annotations


class FactStateResolver:
    """Separate known facts, assumptions, missing facts and stale facts."""

    def resolve(self, facts: list[dict] | None = None, assumptions: list[str] | None = None) -> dict:
        facts = facts or []
        assumptions = assumptions or []
        stale = [f for f in facts if f.get("stale")]
        missing = [a for a in assumptions if a.startswith("need:")]
        return {
            "status": "resolved",
            "known_facts": [f for f in facts if not f.get("stale")],
            "stale_facts": stale,
            "assumptions": assumptions,
            "missing_facts": missing,
            "can_execute_reality_bound_action": not missing and not stale,
        }
