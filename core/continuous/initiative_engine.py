from __future__ import annotations


class InitiativeEngine:
    """Generate proactive but bounded initiatives."""

    def propose(self, attention: dict, budget: dict) -> dict:
        top = attention.get("top", [])
        initiatives = []
        for item in top:
            if item.get("attention_score", 0) >= 80:
                initiatives.append({
                    "title": f"handle_{item.get('type', 'signal')}",
                    "reason": item.get("reason", "high_attention_signal"),
                    "side_effect": False,
                    "requires_confirmation": False,
                })
        if not initiatives:
            initiatives.append({
                "title": "memory_and_goal_maintenance",
                "reason": "low_attention_cycle",
                "side_effect": False,
                "requires_confirmation": False,
            })
        return {
            "status": "initiatives_ready",
            "initiatives": initiatives[:budget.get("budget", {}).get("max_background_checks_per_hour", 4)],
        }
