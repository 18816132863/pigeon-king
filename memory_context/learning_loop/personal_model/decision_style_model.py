from __future__ import annotations


class DecisionStyleModel:
    """Represent the user's decision style without overfitting or fabricating identity."""

    def infer(self, interactions: list[dict]) -> dict:
        directness = "high" if any("直接" in str(i) or "不要猜" in str(i) for i in interactions) else "medium"
        return {
            "directness": directness,
            "confirmation_style": "strong_confirm_for_high_risk_only",
            "automation_preference": "bounded_high_autonomy",
            "artifact_preference": "完整包/可执行文件/一次性方案",
        }
