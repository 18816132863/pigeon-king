"""Personalization engine: preference, risk tolerance, decision style.

This module stores no private data by default. It defines the shape of a profile
that can be filled by approved learning-loop events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PersonalProfile:
    communication_style: str = "direct_concrete_no_repeated_questions"
    autonomy_preference: str = "high_for_low_risk_confirm_for_high_risk"
    risk_tolerance: str = "medium_low_for_irreversible_actions"
    planning_style: str = "one_shot_detailed_execution_package"
    disliked_patterns: list[str] = field(default_factory=lambda: ["反复问", "乱猜", "只说不做", "没有压缩包"])
    preferred_patterns: list[str] = field(default_factory=lambda: ["一次性多给", "明确指令", "可替换包", "先验收再结论"])

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class PersonalizationEngine:
    def __init__(self, profile: PersonalProfile | None = None) -> None:
        self.profile = profile or PersonalProfile()

    def apply_to_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(plan)
        enriched["personalization"] = self.profile.to_dict()
        enriched["interaction_policy"] = {
            "ask_followup_only_if_blocking": True,
            "prefer_concrete_execution": True,
            "prefer_package_delivery": True,
            "avoid_guessing": True,
        }
        return enriched

    def learn_from_feedback(self, feedback: str) -> dict[str, Any]:
        text = feedback or ""
        updates: list[str] = []
        if "不要猜" in text and "不要猜" not in self.profile.disliked_patterns:
            self.profile.disliked_patterns.append("不要猜")
            updates.append("added_dislike:不要猜")
        if "一次性" in text and "一次性" not in self.profile.preferred_patterns:
            self.profile.preferred_patterns.append("一次性")
            updates.append("added_preference:一次性")
        if "自主" in text:
            self.profile.autonomy_preference = "higher_bounded_autonomy"
            updates.append("autonomy_preference:higher_bounded_autonomy")
        return {"status": "learned", "updates": updates, "profile": self.profile.to_dict()}
