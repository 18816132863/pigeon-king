class PersonalFeedbackRouter:
    def route_feedback(self, feedback: dict) -> dict:
        if feedback.get("correction"):
            target = "decision_style_model"
        elif feedback.get("risk_signal"):
            target = "risk_tolerance_model"
        else:
            target = "preference_model"
        return {"status": "routed", "target": target, "feedback": feedback}
