class ProgressEvaluator:
    def evaluate(self, portfolio: dict) -> dict:
        goals = portfolio.get("goals", [])
        total = len(goals)
        done = sum(1 for g in goals if g.get("status") == "done")
        return {
            "status": "evaluated",
            "total_goals": total,
            "done_goals": done,
            "progress_ratio": 0 if total == 0 else done / total,
            "needs_attention": [g for g in goals if g.get("risk_level") in {"L3", "L4", "BLOCKED"}],
        }
