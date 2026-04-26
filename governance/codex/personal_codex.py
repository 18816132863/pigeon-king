"""Personal codex: hard rules + soft preferences + runtime judgement."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Judgement:
    decision: str
    risk_level: str
    reasons: list[str] = field(default_factory=list)
    requires_approval: bool = False
    allowed_auto_steps: list[str] = field(default_factory=list)


class PersonalCodex:
    HARD_CONFIRM_KEYWORDS = ("支付", "转账", "删除", "安装", "发给", "群发", "账号", "密码", "隐私", "交易", "拨打")
    BLOCKED_KEYWORDS = ("绕过确认", "偷", "隐藏记录", "删除审计", "无痕执行")

    def judge_goal(self, goal: str, context: dict[str, Any] | None = None) -> Judgement:
        text = goal or ""
        if any(k in text for k in self.BLOCKED_KEYWORDS):
            return Judgement("blocked", "BLOCKED", ["violates_hard_codex"], True, [])
        hits = [k for k in self.HARD_CONFIRM_KEYWORDS if k in text]
        if hits:
            return Judgement("approval_required", "L3", [f"strong_confirm:{k}" for k in hits], True, ["research", "draft_plan"])
        if "自动" in text or "自己" in text:
            return Judgement("allowed_bounded_autonomy", "L2", ["bounded_autonomy_allowed"], False, ["research", "plan", "safe_probe", "draft"])
        return Judgement("allowed", "L1", ["low_risk_goal"], False, ["research", "plan", "execute_safe", "verify"])
