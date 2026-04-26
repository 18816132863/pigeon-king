from __future__ import annotations

from .what_if_engine import WhatIfEngine
from .outcome_predictor import OutcomePredictor
from .counterfactual_reviewer import CounterfactualReviewer


class ScenarioSimulator:
    """Simulate multiple strategies before choosing an execution path."""

    def __init__(self) -> None:
        self.what_if = WhatIfEngine()
        self.predictor = OutcomePredictor()
        self.reviewer = CounterfactualReviewer()

    def simulate(self, goal: str) -> dict:
        scenarios = self.what_if.generate(goal)
        predictions = [{**s, "prediction": self.predictor.predict(s)} for s in scenarios]
        selected = max(predictions, key=lambda x: x["prediction"]["success_probability"] - (0.2 if x.get("risk_level") == "L3" else 0))
        review = self.reviewer.review(selected, predictions)
        return {
            "status": "simulation_ready",
            "scenarios": predictions,
            "selected": selected,
            "counterfactual_review": review,
        }
