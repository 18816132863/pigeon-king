"""Capability gap detector for self-evolving pending-access agents."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence
from governance.embodied_pending_state import classify_action_semantics

@dataclass
class CapabilityGap:
    name: str
    required_for: str
    semantic_class: str
    risk_level: str
    allowed_growth_path: str
    live_execution_allowed: bool
    reason: str
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class CapabilityGapDetector:
    def detect(self, goal: str, planned_actions: Sequence[Mapping[str, Any]] | None = None, available: Iterable[str] | None = None) -> List[CapabilityGap]:
        available_set = {str(x) for x in (available or [])}
        gaps: List[CapabilityGap] = []
        for action in list(planned_actions or []):
            capability = str(action.get("capability") or action.get("op_name") or action.get("name") or "unknown_capability")
            semantic = classify_action_semantics(action)
            if capability in available_set:
                continue
            if semantic.is_commit_action:
                path = "mock_contract_or_approval_pack_only"
                reason = "missing_commit_capability_may_be_modeled_but_not_live_enabled"
            else:
                path = "trusted_connector_or_sandbox_skill_candidate"
                reason = "missing_non_commit_capability_can_enter_sandbox_evaluation"
            gaps.append(CapabilityGap(capability, goal, semantic.semantic_class, semantic.risk_level, path, False, reason))
        return gaps

def detect_capability_gaps(goal: str, planned_actions: Sequence[Mapping[str, Any]] | None = None, available: Iterable[str] | None = None) -> List[Dict[str, Any]]:
    return [g.to_dict() for g in CapabilityGapDetector().detect(goal, planned_actions, available)]
