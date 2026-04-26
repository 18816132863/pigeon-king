from __future__ import annotations


class AutonomyLevelPolicy:
    """Define how far the agent can go without asking."""

    LEVELS = {
        "manual": {"auto_execute": False, "auto_search": False, "auto_extend": False},
        "assisted": {"auto_execute": False, "auto_search": True, "auto_extend": False},
        "bounded_high": {"auto_execute": True, "auto_search": True, "auto_extend": "sandbox_only"},
        "supervised_auto": {"auto_execute": True, "auto_search": True, "auto_extend": "approval_required"},
    }

    def resolve(self, level: str = "bounded_high") -> dict:
        return {"level": level, **self.LEVELS.get(level, self.LEVELS["bounded_high"])}
