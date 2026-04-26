class AutonomousProjectReview:
    def review(self, project: dict, milestones: dict) -> dict:
        risks = [m["risk"] for m in milestones.get("milestones", [])]
        return {
            "status": "reviewed",
            "max_risk": "L3" if "L3" in risks else "L2" if "L2" in risks else "L1",
            "needs_external_validation": any(m["milestone"] == "validate_real_runtime" for m in milestones.get("milestones", [])),
            "strong_confirm_required": "L3" in risks,
        }
