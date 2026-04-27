"""V30.0 Constitutional Judge V4.

L5 Governance:
- Hard law: never violate.
- Soft preference: user style and risk tolerance.
- Situational judge: runtime context.
- Tool/action guardrails must be called before each side effect action.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, List


@dataclass
class JudgeDecision:
    decision: str  # allow / confirm / deny
    risk_tier: str
    reason: str
    required_controls: List[str]

    def to_dict(self):
        return asdict(self)


class ConstitutionalJudgeV4:
    destructive_terms = ("delete", "wipe", "payment", "transfer", "privacy_export", "unknown_install", "删除", "清空", "支付", "转账")
    side_effect_terms = ("device_action", "send_message", "calendar", "alarm", "notification", "file_write", "settings_change", "gui_action")

    def judge(self, action_kind: str, context: Dict[str, Any]) -> JudgeDecision:
        # Hard law first.
        if action_kind in self.destructive_terms or context.get("destructive") is True:
            return JudgeDecision("confirm", "L4", "destructive or sensitive action requires strong confirmation", ["strong_confirmation", "audit", "rollback_plan"])

        if action_kind == "unknown_code_install":
            if context.get("sandboxed") and context.get("hash_verified") and context.get("rollback_ready"):
                return JudgeDecision("confirm", "L4", "sandboxed extension can only proceed with approval", ["sandbox", "hash_verify", "min_test", "human_approval"])
            return JudgeDecision("deny", "L4", "unknown code install without sandbox controls", ["deny"])

        if action_kind in self.side_effect_terms or context.get("side_effect") is True:
            controls = ["idempotency_key", "receipt", "verification_policy", "audit"]
            if context.get("device_side_effect"):
                controls.append("global_device_serial_lane")
            return JudgeDecision("allow", "L2", "side effect allowed with controls", controls)

        if context.get("confidence", 1.0) < 0.55:
            return JudgeDecision("confirm", "L3", "low confidence requires user approval", ["ask_or_verify"])

        return JudgeDecision("allow", "L1", "low risk internal action", ["trace"])
