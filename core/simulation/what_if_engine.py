class WhatIfEngine:
    def generate(self, goal: str) -> list[dict]:
        return [
            {"scenario": "use_existing_capability", "risk_level": "L1", "cost": "low"},
            {"scenario": "search_solution_first", "risk_level": "L2", "cost": "medium"},
            {"scenario": "connect_external_capability", "risk_level": "L3", "cost": "medium", "confirmation_required": True},
        ]
