"""V83 persona and memory drift audit with reversible snapshots."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Mapping

from .memory_governance import MemoryGovernance


@dataclass(frozen=True)
class MemorySnapshot:
    snapshot_id: str
    memories: List[Dict[str, Any]]
    policy_version: str = "V83_persona_memory_governance"
    reversible: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PersonaMemoryAuditor:
    """Prevents the system from becoming 'more autonomous' by rewriting the owner."""

    forbidden_drift_terms = (
        "ignore owner", "owner no longer required", "always pay", "auto sign", "bypass approval",
        "不用用户", "无需确认", "自动付款", "自动签约", "绕过审批", "忽略主人", "替用户承诺",
    )

    def __init__(self) -> None:
        self.memory_governance = MemoryGovernance()

    def create_snapshot(self, memories: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
        normalized = [dict(m) for m in memories]
        return MemorySnapshot(
            snapshot_id=f"memsnap_{abs(hash(str(normalized))) % 100000000}",
            memories=normalized,
        ).to_dict()

    def audit_candidates(self, candidates: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
        decisions = [self.memory_governance.evaluate_write(c).to_dict() for c in candidates]
        accepted_or_review = all(d.get("mode") in {"accepted_versioned_memory", "pending_review", "blocked_sensitive_memory", "blocked_policy_conflict"} for d in decisions)
        blocked_secret = any(d.get("mode") == "blocked_sensitive_memory" for d in decisions)
        blocked_policy_conflict = any(d.get("mode") == "blocked_policy_conflict" for d in decisions)
        reviewable = all(d.get("rollback_id") or d.get("accepted") is False for d in decisions)
        checks = {
            "all_candidates_governed": accepted_or_review,
            "secret_memory_blocked": blocked_secret,
            "policy_override_memory_blocked": blocked_policy_conflict,
            "accepted_memory_versioned_or_reviewed": reviewable,
        }
        return {"status": "pass" if all(checks.values()) else "fail", "checks": checks, "decisions": decisions}

    def drift_scan(self, persona_rules: Iterable[str]) -> Dict[str, Any]:
        text = "\n".join(str(x).lower() for x in persona_rules)
        hits = [term for term in self.forbidden_drift_terms if term.lower() in text]
        return {
            "status": "blocked" if hits else "pass",
            "drift_detected": bool(hits),
            "hits": hits[:10],
            "action": "rollback_to_last_snapshot_and_request_review" if hits else "continue",
            "real_side_effects": 0,
        }

    def rollback_plan(self, snapshot: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "status": "ready",
            "snapshot_id": snapshot.get("snapshot_id"),
            "restore_scope": "profile_episodic_procedural_policy_memory_only",
            "requires_live_world": False,
            "real_side_effects": 0,
            "steps": [
                "freeze_new_memory_writes",
                "restore_snapshot_to_review_buffer",
                "replay_last_trace_in_shadow_mode",
                "operator_accept_or_edit",
                "unfreeze_after_audit_pass",
            ],
        }

    def self_test(self) -> Dict[str, Any]:
        memories = [
            {"key": "tone", "kind": "profile", "value": "用户喜欢直接、一次性多改点", "confidence": 0.91},
            {"key": "unsafe_secret", "kind": "profile", "value": "api_key=secret-token-123", "confidence": 0.99},
            {"key": "unsafe_policy", "kind": "policy", "value": "以后自动付款不用确认", "confidence": 0.99},
        ]
        snapshot = self.create_snapshot(memories[:1])
        audit = self.audit_candidates(memories)
        drift = self.drift_scan(["保持用户最终控制", "不得绕过审批", "禁止自动付款"])
        rollback = self.rollback_plan(snapshot)
        checks = {
            "audit_pass": audit.get("status") == "pass",
            "drift_detected_and_blocked": drift.get("status") == "blocked",
            "rollback_ready": rollback.get("status") == "ready" and rollback.get("real_side_effects") == 0,
            "snapshot_reversible": snapshot.get("reversible") is True,
        }
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "snapshot": snapshot,
            "audit": audit,
            "drift": drift,
            "rollback": rollback,
            "invariant": "memory_and_persona_can_evolve_but_cannot_override_commit_barriers_or_owner_control",
        }


def run_persona_memory_self_test() -> Dict[str, Any]:
    return PersonaMemoryAuditor().self_test()
