from __future__ import annotations


class MissionPriorityEngine:
    def score(self, mission: dict) -> dict:
        risk_penalty = {"L0": 0, "L1": 5, "L2": 15, "L3": 35, "L4": 60, "BLOCKED": 100}
        nodes = mission.get("nodes", [])
        max_risk = "L1"
        for node in nodes:
            risk = node.get("risk_level", "L1")
            if risk_penalty.get(risk, 10) > risk_penalty.get(max_risk, 10):
                max_risk = risk
        urgency = 80 if "紧急" in mission.get("objective", "") else 50
        score = urgency - risk_penalty.get(max_risk, 10)
        return {"priority_score": score, "max_risk": max_risk, "urgency": urgency}
