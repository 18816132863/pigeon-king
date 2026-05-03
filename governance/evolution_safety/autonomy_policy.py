"""Autonomy-level policy for keeping the system powerful but not live-dangerous."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping

@dataclass(frozen=True)
class AutonomyPolicyDecision:
    autonomy_level: str
    allowed: bool
    max_effect: str
    reason: str
    requires_human: bool
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class AutonomyLevelPolicy:
    MAX_PENDING_LEVEL = 3
    def evaluate(self, request: Mapping[str, Any] | None = None) -> AutonomyPolicyDecision:
        request = dict(request or {})
        level = request.get("autonomy_level", request.get("level", "L3"))
        if isinstance(level, str) and level.upper().startswith("L"):
            try:
                numeric = int(level.upper().replace("L", ""))
            except ValueError:
                numeric = 3
        else:
            numeric = int(level or 3)
        if numeric <= self.MAX_PENDING_LEVEL:
            return AutonomyPolicyDecision(f"L{numeric}", True, "sandbox_shadow_prepare_only", "pending_access_state_allows_observe_reason_generate_prepare_simulate_shadow", False)
        return AutonomyPolicyDecision(f"L{numeric}", False, "approval_pack_only_no_live_commit", "requested_autonomy_exceeds_pending_access_freeze_boundary", True)

def evaluate_autonomy(request: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    return AutonomyLevelPolicy().evaluate(request).to_dict()
