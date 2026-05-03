"""Operating constitution for the pending-access embodied intelligence state.

V79 adds a constitution layer above the commit barrier.  It does not grant live
power.  It proves every action is governed by explicit hard laws, soft user
preferences and contextual escalation rules before any runtime tries to prepare
or simulate the action.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Sequence

from governance.embodied_pending_state import classify_action_semantics


HARD_LAWS: Sequence[Dict[str, Any]] = (
    {
        "law_id": "HARD-001",
        "name": "no_real_money_without_final_switch_and_dual_key",
        "classes": {"payment"},
        "decision": "hard_stop",
        "reason": "spending, transfer, checkout and refund actions must stop before commit",
    },
    {
        "law_id": "HARD-002",
        "name": "no_signature_or_contract_without_dual_key",
        "classes": {"signature", "identity_commit"},
        "decision": "hard_stop",
        "reason": "legal or identity commitments must stay as approval packets",
    },
    {
        "law_id": "HARD-003",
        "name": "no_physical_actuation_while_pending",
        "classes": {"physical_actuation"},
        "decision": "hard_stop",
        "reason": "robots, devices, doors, vehicles and motors remain mock-only",
    },
    {
        "law_id": "HARD-004",
        "name": "no_destructive_change_without_review",
        "classes": {"destructive"},
        "decision": "hard_stop",
        "reason": "delete, wipe, revoke and irreversible changes must not execute live",
    },
    {
        "law_id": "HARD-005",
        "name": "external_send_is_draft_only",
        "classes": {"external_send"},
        "decision": "approval_packet",
        "reason": "mail, post, webhook, notification and public messages require review",
    },
)

SOFT_PREFERENCES: Sequence[Dict[str, Any]] = (
    {
        "preference_id": "SOFT-001",
        "name": "default_to_less_questioning_but_more_guarded_execution",
        "applies_to": "all",
        "decision": "prefer_prepare_then_stop",
    },
    {
        "preference_id": "SOFT-002",
        "name": "produce_direct_artifacts_for_technical_partners",
        "applies_to": "generate_prepare_simulate",
        "decision": "prefer_file_like_deliverables_and_patch_overlays",
    },
    {
        "preference_id": "SOFT-003",
        "name": "no_real_world_connection_until_explicit_release",
        "applies_to": "all",
        "decision": "shadow_mode_first",
    },
)

CONTEXT_RULES: Sequence[Dict[str, Any]] = (
    {
        "rule_id": "CTX-001",
        "name": "unknown_or_ambiguous_action_escalates",
        "condition": "semantic_class_unknown",
        "decision": "pause_for_review",
    },
    {
        "rule_id": "CTX-002",
        "name": "live_credential_request_escalates",
        "condition": "action_requests_live_credentials",
        "decision": "pause_for_security_review",
    },
    {
        "rule_id": "CTX-003",
        "name": "memory_or_policy_mutation_requires_audit",
        "condition": "action_modifies_memory_policy_or_permissions",
        "decision": "audit_and_approval_packet",
    },
)


@dataclass(frozen=True)
class ConstitutionDecision:
    allowed_to_prepare: bool
    allowed_to_execute_live: bool
    constitutional_decision: str
    semantic_class: str
    risk_level: str
    matched_hard_laws: List[Dict[str, Any]]
    matched_soft_preferences: List[Dict[str, Any]]
    matched_context_rules: List[Dict[str, Any]]
    proof_obligations: List[str]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OperatingConstitution:
    """Policy constitution: hard laws first, preferences second, context last."""

    def evaluate(self, action: Mapping[str, Any] | None, context: Mapping[str, Any] | None = None) -> ConstitutionDecision:
        action = dict(action or {})
        context = dict(context or {})
        semantic = classify_action_semantics(action)
        semantic_class = semantic.semantic_class

        matched_hard = [{**dict(law), "classes": sorted(list(law["classes"]))} for law in HARD_LAWS if semantic_class in law["classes"]]
        matched_soft = [dict(pref) for pref in SOFT_PREFERENCES if pref["applies_to"] in {"all", semantic_class, "generate_prepare_simulate"}]
        matched_context: List[Dict[str, Any]] = []
        if semantic_class == "unknown":
            matched_context.append(dict(CONTEXT_RULES[0]))
        if action.get("wants_live_credentials") or action.get("live_credentials"):
            matched_context.append(dict(CONTEXT_RULES[1]))
        if action.get("modifies_policy") or action.get("modifies_memory") or action.get("permission_change"):
            matched_context.append(dict(CONTEXT_RULES[2]))

        if matched_hard:
            decision = "hard_stop" if any(law["decision"] == "hard_stop" for law in matched_hard) else "approval_packet_only"
            allowed_to_prepare = True
            allowed_live = False
            reason = "hard_law_matched_commit_must_not_execute_live"
        elif matched_context:
            decision = "pause_for_review"
            allowed_to_prepare = False
            allowed_live = False
            reason = "context_rule_requires_review"
        elif semantic.allowed_in_pending_access_state:
            decision = "prepare_or_sandbox_allowed"
            allowed_to_prepare = True
            allowed_live = False
            reason = "non_commit_action_allowed_in_pending_access_state"
        else:
            decision = "pause_for_review"
            allowed_to_prepare = False
            allowed_live = False
            reason = "unclassified_action_requires_review"

        obligations = [
            "action_semantic_recorded",
            "commit_barrier_result_recorded",
            "freeze_switch_closed_recorded",
            "audit_event_append_only",
        ]
        if semantic.is_commit_action:
            obligations.extend(["approval_packet_created", "real_side_effect_zero", "rollback_or_mock_plan_attached"])
        if matched_context:
            obligations.append("human_review_reason_attached")

        return ConstitutionDecision(
            allowed_to_prepare=allowed_to_prepare,
            allowed_to_execute_live=allowed_live,
            constitutional_decision=decision,
            semantic_class=semantic_class,
            risk_level=semantic.risk_level,
            matched_hard_laws=matched_hard,
            matched_soft_preferences=matched_soft,
            matched_context_rules=matched_context,
            proof_obligations=obligations,
            reason=reason,
        )


def evaluate_constitution(action: Mapping[str, Any] | None, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    return OperatingConstitution().evaluate(action, context).to_dict()
