"""V81 permission leases and dual-key approval envelopes.

The pending-access system may understand and prepare full-permission workflows,
but every permission is time/scope bounded and all commit actions remain blocked
until the final live-access switch is intentionally opened outside this state.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

from governance.embodied_pending_state.action_semantics import (
    ALLOWED_PENDING_CLASSES,
    COMMIT_CLASSES,
    HARD_STOP_CLASSES,
    SemanticClass,
    classify_action_semantics,
)
from governance.embodied_pending_state.commit_barrier import CommitBarrier


@dataclass(frozen=True)
class PermissionLease:
    lease_id: str
    subject: str
    purpose: str
    allowed_semantic_classes: List[str]
    forbidden_semantic_classes: List[str]
    max_autonomy_level: str = "L3"
    expires_policy: str = "session_or_24h_whichever_first"
    live_world_enabled: bool = False
    payment_enabled: bool = False
    signature_enabled: bool = False
    physical_actuation_enabled: bool = False
    external_send_enabled: bool = False
    audit_required: bool = True
    rollback_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PermissionLeaseDecision:
    allowed_by_lease: bool
    blocked_by_barrier: bool
    final_allowed: bool
    semantic_class: str
    risk_level: str
    lease_id: str
    reason: str
    next_safe_action: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DualKeyApprovalEnvelope:
    envelope_id: str
    action_summary: str
    semantic_class: str
    first_key_required: str
    second_key_required: str
    expires_policy: str
    can_execute_in_pending_access_state: bool
    real_side_effect_allowed: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PermissionLeaseManager:
    """Issues scoped leases and proves commit actions cannot bypass the barrier."""

    def create_default_pending_access_lease(self, subject: str = "owner_ai_runtime") -> PermissionLease:
        allowed = sorted(cls.value for cls in ALLOWED_PENDING_CLASSES)
        forbidden = sorted(cls.value for cls in COMMIT_CLASSES)
        return PermissionLease(
            lease_id="lease_pending_access_default_v81",
            subject=subject,
            purpose="full_function_dry_run_shadow_and_preparation_without_live_commit",
            allowed_semantic_classes=allowed,
            forbidden_semantic_classes=forbidden,
        )

    def evaluate(self, action: Mapping[str, Any], lease: Optional[PermissionLease] = None) -> PermissionLeaseDecision:
        lease = lease or self.create_default_pending_access_lease()
        semantic = classify_action_semantics(action)
        barrier = CommitBarrier().check(action)
        allowed_by_lease = semantic.semantic_class in lease.allowed_semantic_classes and semantic.semantic_class not in lease.forbidden_semantic_classes
        final_allowed = allowed_by_lease and barrier.allowed and not barrier.real_side_effect_allowed
        if final_allowed:
            reason = "leased_non_commit_action_allowed_only_in_sandbox_or_preparation_mode"
            next_safe = "execute_dry_run_or_prepare_artifact"
        elif semantic.semantic_class in lease.forbidden_semantic_classes:
            reason = "semantic_class_forbidden_by_pending_access_lease"
            next_safe = "create_dual_key_approval_envelope_or_mock_contract_only"
        elif barrier.is_commit_action:
            reason = "commit_barrier_blocks_real_side_effect_even_if_future_permission_exists"
            next_safe = barrier.next_safe_action
        else:
            reason = "unleased_or_unknown_action_requires_review"
            next_safe = "manual_classification_review"
        return PermissionLeaseDecision(
            allowed_by_lease=allowed_by_lease,
            blocked_by_barrier=not barrier.allowed,
            final_allowed=final_allowed,
            semantic_class=semantic.semantic_class,
            risk_level=semantic.risk_level,
            lease_id=lease.lease_id,
            reason=reason,
            next_safe_action=next_safe,
        )

    def build_dual_key_envelope(self, action: Mapping[str, Any], *, reason: str = "pending_access_commit_action") -> DualKeyApprovalEnvelope:
        semantic = classify_action_semantics(action)
        return DualKeyApprovalEnvelope(
            envelope_id=f"dual_key_{abs(hash(str(sorted(dict(action).items())))) % 100000000}",
            action_summary=str(action.get("summary") or action.get("op_name") or action),
            semantic_class=semantic.semantic_class,
            first_key_required="owner_explicit_confirmation",
            second_key_required="risk_controller_or_policy_admin_confirmation",
            expires_policy="single_action_short_lived_never_reusable",
            can_execute_in_pending_access_state=False,
            real_side_effect_allowed=False,
            reason=reason,
        )

    def self_test(self) -> Dict[str, Any]:
        lease = self.create_default_pending_access_lease()
        probes = [
            {"op_name": "read_status", "summary": "读取状态"},
            {"op_name": "draft_email", "summary": "起草邮件", "semantic_class": "generate"},
            {"op_name": "send_email", "summary": "对外发送邮件"},
            {"op_name": "pay_invoice", "summary": "支付发票", "payment": True},
            {"op_name": "sign_contract", "summary": "签署合同"},
            {"op_name": "move_robot_arm", "summary": "机械臂移动", "physical_actuation": True},
        ]
        decisions = [self.evaluate(p, lease).to_dict() for p in probes]
        envelopes = [self.build_dual_key_envelope(p).to_dict() for p in probes if classify_action_semantics(p).is_commit_action]
        checks = {
            "lease_scope_declared": bool(lease.allowed_semantic_classes and lease.forbidden_semantic_classes),
            "non_commit_allowed_only_without_real_side_effect": all(d["final_allowed"] is True for d in decisions[:2]),
            "commit_actions_denied_by_lease": all(d["final_allowed"] is False for d in decisions[2:]),
            "commit_actions_have_dual_key_envelopes": len(envelopes) == 4 and all(e["can_execute_in_pending_access_state"] is False for e in envelopes),
            "payment_signature_physical_live_flags_false": not lease.payment_enabled and not lease.signature_enabled and not lease.physical_actuation_enabled,
        }
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "lease": lease.to_dict(),
            "decisions": decisions,
            "dual_key_envelopes": envelopes,
            "invariant": "leases_prepare_permission_shape_without_granting_live_commit_power",
        }


def run_permission_lease_self_test() -> Dict[str, Any]:
    return PermissionLeaseManager().self_test()
