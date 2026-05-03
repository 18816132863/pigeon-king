"""AntiContextAmnesiaGuard — 防上下文失忆守卫

检查当前回答是否因上下文不足而失忆。
如果 handoff / capsule 存在但回答显示失忆，则触发纠正。
"""
from __future__ import annotations
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Optional

CONTEXT_DIR = Path.cwd() / ".context_state"


@dataclass
class AmnesiaCheckResult:
    guarded: bool = False
    handoff_available: bool = False
    capsule_available: bool = False
    amnesia_detected: bool = False
    recommended_action: str = "proceed"
    note: str = ""


class AntiContextAmnesiaGuard:
    def __init__(self):
        self.handoff_path = CONTEXT_DIR / "session_handoff_latest.json"
        self.capsule_path = CONTEXT_DIR / "context_capsule.json"

    def check(self, user_message: str = "") -> AmnesiaCheckResult:
        handoff_available = self.handoff_path.exists()
        capsule_available = self.capsule_path.exists()

        if not handoff_available and not capsule_available:
            return AmnesiaCheckResult(guarded=True, handoff_available=False, capsule_available=False,
                                      amnesia_detected=False, recommended_action="proceed",
                                      note="No handoff or capsule available, proceeding fresh.")

        amnesia_triggers = ["继续", "上一步", "刚才", "这个包", "这个版本",
                            "我们之前", "上次说到", "上回", "前一次"]
        triggered = any(kw in user_message for kw in amnesia_triggers)

        if triggered:
            if handoff_available:
                return AmnesiaCheckResult(guarded=True, handoff_available=True, capsule_available=capsule_available,
                                          amnesia_detected=False, recommended_action="read_handoff",
                                          note=f"User said '{user_message[:30]}' — handoff available, should read before replying.")
            elif capsule_available:
                return AmnesiaCheckResult(guarded=True, handoff_available=False, capsule_available=True,
                                          amnesia_detected=False, recommended_action="read_capsule",
                                          note="User referenced previous context, handoff not found, read capsule.")
            else:
                return AmnesiaCheckResult(guarded=True, handoff_available=False, capsule_available=False,
                                          amnesia_detected=True, recommended_action="proceed",
                                          note="User referenced previous context but no handoff/capsule found. Consider flagging.")

        return AmnesiaCheckResult(guarded=True, handoff_available=handoff_available, capsule_available=capsule_available,
                                  amnesia_detected=False, recommended_action="read_handoff" if handoff_available else "proceed",
                                  note="No amnesia triggers detected.")

    def get_handoff_summary(self) -> str | None:
        if not self.handoff_path.exists():
            return None
        try:
            data = json.loads(self.handoff_path.read_text(encoding="utf-8"))
            parts = []
            if data.get("user_real_goal"):
                parts.append(f"用户目标: {data['user_real_goal']}")
            if data.get("current_blocker"):
                parts.append(f"卡点: {data['current_blocker']}")
            if data.get("next_continue_from"):
                parts.append(f"下一步: {data['next_continue_from']}")
            if data.get("do_not_repeat"):
                parts.append(f"不要重复: {', '.join(data['do_not_repeat'][:3])}")
            return " | ".join(parts) if parts else "Handoff exists but no actionable context."
        except Exception:
            return "Handoff exists but could not be parsed."

    def get_capsule_summary(self) -> str | None:
        if not self.capsule_path.exists():
            return None
        try:
            data = json.loads(self.capsule_path.read_text(encoding="utf-8"))
            parts = []
            if data.get("current_goal"):
                parts.append(f"目标: {data['current_goal'][:60]}")
            if data.get("next_best_action"):
                parts.append(f"建议: {data['next_best_action'][:60]}")
            if data.get("active_constraints"):
                parts.append(f"约束: {len(data['active_constraints'])}条")
            if data.get("must_not_repeat"):
                parts.append(f"勿重复: {len(data['must_not_repeat'])}条")
            return " | ".join(parts) if parts else "Capsule exists but minimal context."
        except Exception:
            return "Capsule exists but could not be parsed."


_amnesia_guard: AntiContextAmnesiaGuard | None = None


def get_anti_context_amnesia_guard() -> AntiContextAmnesiaGuard:
    global _amnesia_guard
    if _amnesia_guard is None:
        _amnesia_guard = AntiContextAmnesiaGuard()
    return _amnesia_guard
