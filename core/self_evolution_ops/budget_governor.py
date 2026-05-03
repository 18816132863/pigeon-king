from __future__ import annotations

from .schemas import BudgetDecision, BudgetStatus, new_id


class BudgetGovernor:
    """V110: token/cost/time budget governor."""

    def decide(self, task_type: str, complexity: str = "medium", cost_preference: str = "balanced") -> BudgetDecision:
        base_tokens = {"low": 3000, "medium": 9000, "high": 24000, "very_high": 64000}.get(complexity, 9000)
        base_cost = {"low": 0.03, "medium": 0.20, "high": 1.20, "very_high": 4.00}.get(complexity, 0.20)
        time_budget = {"low": 20, "medium": 60, "high": 180, "very_high": 420}.get(complexity, 60)

        if cost_preference == "low":
            token_budget = max(1500, int(base_tokens * 0.45))
            cost_budget = round(base_cost * 0.35, 4)
            model_group = "fast_low_cost"
            status = BudgetStatus.NEEDS_DOWNGRADE if complexity in {"high", "very_high"} else BudgetStatus.WITHIN_BUDGET
            reason = "low cost preference selected"
        elif cost_preference == "quality":
            token_budget = int(base_tokens * 1.4)
            cost_budget = round(base_cost * 1.8, 4)
            model_group = "reasoning_high"
            status = BudgetStatus.WITHIN_BUDGET
            reason = "quality preference selected"
        else:
            token_budget = base_tokens
            cost_budget = base_cost
            model_group = "balanced_reasoning"
            status = BudgetStatus.WITHIN_BUDGET
            reason = "balanced budget"

        if cost_budget > 5.0:
            status = BudgetStatus.BLOCKED_OVER_BUDGET
            reason = "estimated cost exceeds hard budget"

        return BudgetDecision(
            id=new_id("budget"),
            task_type=task_type,
            token_budget=token_budget,
            cost_budget=cost_budget,
            time_budget_seconds=time_budget,
            status=status,
            recommended_model_group=model_group,
            reason=reason,
        )
