from __future__ import annotations

from typing import Any
from .personal_codex import PersonalCodex


class JudgementEngine:
    def __init__(self, codex: PersonalCodex | None = None) -> None:
        self.codex = codex or PersonalCodex()

    def judge(self, goal: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        judgement = self.codex.judge_goal(goal, context)
        return {
            "decision": judgement.decision,
            "risk_level": judgement.risk_level,
            "reasons": judgement.reasons,
            "requires_approval": judgement.requires_approval,
            "allowed_auto_steps": judgement.allowed_auto_steps,
        }
