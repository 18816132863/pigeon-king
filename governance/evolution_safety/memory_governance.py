"""Governed long-term memory writeback for the self-evolving pending-access shape."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional

class MemoryKind(str, Enum):
    PROFILE = "profile"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    POLICY = "policy"
    TEMPORARY = "temporary"

SENSITIVE_MEMORY_TERMS = (
    "password", "passwd", "secret", "token", "api_key", "private_key", "cookie",
    "credential", "access_token", "refresh_token", "card_number", "cvv", "pin",
    "身份证", "银行卡", "密码", "密钥", "令牌", "凭证", "验证码", "支付密码",
)
CONTRADICTORY_COMMIT_TERMS = (
    "always pay", "auto pay", "auto purchase", "never ask before paying", "sign for me",
    "自动支付", "自动付款", "自动下单", "不用确认直接付款", "替我签", "自动签约",
)

@dataclass
class MemoryCandidate:
    key: str
    kind: str
    value: Any
    source: str = "runtime"
    confidence: float = 0.5
    ttl_days: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class MemoryGovernanceDecision:
    accepted: bool
    mode: str
    reason: str
    review_required: bool
    rollback_id: Optional[str]
    normalized_memory: Optional[Dict[str, Any]]
    blocked_terms: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class MemoryGovernance:
    def evaluate_write(self, candidate: Mapping[str, Any] | MemoryCandidate) -> MemoryGovernanceDecision:
        raw = candidate.to_dict() if isinstance(candidate, MemoryCandidate) else dict(candidate or {})
        text = " ".join(str(v) for v in raw.values()).lower()
        blocked = [term for term in SENSITIVE_MEMORY_TERMS if term.lower() in text]
        if blocked:
            return MemoryGovernanceDecision(False, "blocked_sensitive_memory", "long_term_memory_must_not_store_credentials_payment_secrets_or_raw_private_keys", True, None, None, blocked[:8])
        conflicts = [term for term in CONTRADICTORY_COMMIT_TERMS if term.lower() in text]
        if conflicts:
            return MemoryGovernanceDecision(False, "blocked_policy_conflict", "memory_cannot_override_payment_signature_or_commit_barrier_policy", True, None, None, conflicts[:8])
        kind = str(raw.get("kind") or MemoryKind.TEMPORARY.value)
        try:
            kind = MemoryKind(kind).value
        except ValueError:
            kind = MemoryKind.TEMPORARY.value
        confidence = float(raw.get("confidence", 0.5) or 0.5)
        review_required = kind in {MemoryKind.PROFILE.value, MemoryKind.POLICY.value, MemoryKind.PROCEDURAL.value} or confidence < 0.72
        ttl = raw.get("ttl_days")
        if kind == MemoryKind.TEMPORARY.value and ttl is None:
            ttl = 7
        normalized = {
            "key": str(raw.get("key") or "memory_candidate"),
            "kind": kind,
            "value": raw.get("value"),
            "source": str(raw.get("source") or "runtime"),
            "confidence": round(max(0.0, min(1.0, confidence)), 4),
            "ttl_days": ttl,
            "tags": list(raw.get("tags") or []),
            "state": "pending_review" if review_required else "accepted",
            "versioned": True,
            "reversible": True,
        }
        return MemoryGovernanceDecision(
            accepted=not review_required,
            mode="pending_review" if review_required else "accepted_versioned_memory",
            reason="stable_memory_requires_review" if review_required else "safe_low_risk_memory_write_allowed",
            review_required=review_required,
            rollback_id=f"mem_rb_{abs(hash(str(normalized))) % 100000000}",
            normalized_memory=normalized,
        )

def evaluate_memory_write(candidate: Mapping[str, Any] | MemoryCandidate) -> Dict[str, Any]:
    return MemoryGovernance().evaluate_write(candidate).to_dict()
