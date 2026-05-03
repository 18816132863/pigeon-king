# -*- coding: utf-8 -*-
"""V86 policy judge: hard code + risk tier + approval decision."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .schemas import Decision, PolicyDecision, RiskLevel, TaskNode


class PolicyJudge:
    HARD_BLOCK_ACTIONS = {
        "bypass_auth",
        "exfiltrate_secret",
        "disable_safety",
        "steal_credentials",
        "malware_execution",
        "irreversible_delete_without_backup",
    }

    STRONG_APPROVAL_RISKS = {"money", "delete", "install_code", "privacy", "system_change"}
    APPROVAL_RISKS = {"external_send"}

    def decide(self, action: Dict[str, Any] | TaskNode, context: Dict[str, Any] | None = None) -> PolicyDecision:
        context = context or {}
        if isinstance(action, TaskNode):
            payload = {
                "action": action.action,
                "risk_hints": self._risk_hints_from_node(action),
                "risk_level": action.risk_level.value,
                "external": action.requires_approval,
            }
        else:
            payload = dict(action)

        action_name = str(payload.get("action", "unknown"))
        risk_hints = set(payload.get("risk_hints") or [])

        if action_name in self.HARD_BLOCK_ACTIONS or risk_hints & {"hard_block"}:
            return PolicyDecision(
                decision=Decision.BLOCK,
                risk_level=RiskLevel.L5,
                reasons=["hard_codex_block"],
                approval_required=False,
                strong_approval_required=False,
                can_auto_execute=False,
            )

        if context.get("context_confidence", 1.0) < 0.55:
            return PolicyDecision(
                decision=Decision.REQUIRE_CLARIFICATION,
                risk_level=RiskLevel.L2,
                reasons=["low_context_confidence"],
                approval_required=False,
                can_auto_execute=False,
            )

        if risk_hints & self.STRONG_APPROVAL_RISKS:
            return PolicyDecision(
                decision=Decision.REQUIRE_STRONG_APPROVAL,
                risk_level=RiskLevel.L4,
                reasons=["strong_approval_required_by_risk"],
                approval_required=True,
                strong_approval_required=True,
                can_auto_execute=False,
            )

        if risk_hints & self.APPROVAL_RISKS or payload.get("external"):
            return PolicyDecision(
                decision=Decision.REQUIRE_APPROVAL,
                risk_level=RiskLevel.L3,
                reasons=["approval_required_for_external_side_effect"],
                approval_required=True,
                strong_approval_required=False,
                can_auto_execute=False,
            )

        if payload.get("mutates_state"):
            return PolicyDecision(
                decision=Decision.PREVIEW_ONLY,
                risk_level=RiskLevel.L2,
                reasons=["state_mutation_requires_preview"],
                approval_required=False,
                can_auto_execute=False,
            )

        return PolicyDecision(
            decision=Decision.ALLOW,
            risk_level=RiskLevel.L1,
            reasons=["safe_low_risk_auto_allowed"],
            approval_required=False,
            strong_approval_required=False,
            can_auto_execute=True,
        )

    def decide_goal_risk(self, risk_hints: Iterable[str], context: Dict[str, Any] | None = None) -> PolicyDecision:
        return self.decide({"action": "goal", "risk_hints": list(risk_hints)}, context=context)

    def _risk_hints_from_node(self, node: TaskNode) -> List[str]:
        hints = []
        if node.risk_level == RiskLevel.L4:
            hints.append("system_change")
        elif node.risk_level == RiskLevel.L3:
            hints.append("external_send")
        if node.requires_approval:
            hints.append("external_send")
        return hints or ["low"]
