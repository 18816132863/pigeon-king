class PromptStrategyOptimizer:
    def optimize(self, user_style: dict) -> dict:
        if user_style.get("directness") == "high":
            style = "direct_artifact_first"
        else:
            style = "balanced_explanation_then_action"
        return {
            "status": "optimized",
            "response_strategy": style,
            "avoid": ["unnecessary_clarification", "vague_next_steps", "unsupported_claims"],
        }
