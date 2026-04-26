from __future__ import annotations


class RuntimeBudgetManager:
    """Token/time/action budget guard for always-on autonomy."""

    DEFAULT_BUDGET = {
        "max_background_checks_per_hour": 4,
        "max_external_reads_per_cycle": 3,
        "max_external_writes_without_confirmation": 0,
        "max_device_actions_without_confirmation": 0,
        "max_cost_without_confirmation": 0,
    }

    def allocate(self, mode: str = "bounded_high") -> dict:
        budget = dict(self.DEFAULT_BUDGET)
        if mode == "quiet":
            budget["max_background_checks_per_hour"] = 1
        if mode == "intensive":
            budget["max_background_checks_per_hour"] = 8
            budget["max_external_reads_per_cycle"] = 6
        return {"status": "budget_allocated", "mode": mode, "budget": budget}
