"""ContinuitySummary — 连续性摘要

每次会话开始时生成上下文摘要，
供 mainline_hook 加载，用于保持人格连续性和交互一致性。

包含 V102 的签名功能用于人格偏移检测。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

PERSONA_DIR = Path.cwd() / ".memory_persona"
PERSONA_DIR.mkdir(parents=True, exist_ok=True)


class ContinuitySummary:
    """连续性摘要"""

    def __init__(self):
        self.summary_path = PERSONA_DIR / "continuity_summary.json"

    def generate(self, persona_state: dict, relationship_summary: dict,
                 last_goal: str = "", last_tasks: list[str] | None = None,
                 voice_guidance: str = "") -> dict:
        summary = {
            "who_am_i": "九尾赛博狐狸 AI 助手 · 鸽子王 🦊",
            "who_is_user": self._describe_user(relationship_summary),
            "what_we_were_doing": last_goal or "新会话，无上次活动记录",
            "last_blocker_or_failure": relationship_summary.get("last_failure"),
            "current_most_important_goal": self._get_most_important_goal(persona_state, relationship_summary),
            "current_forbidden_actions": [
                "真实支付、转账、金融交易",
                "真实发送消息/邮件/公开发布",
                "真实控制设备、硬件、机器人",
                "签署合同或法律承诺",
                "声明自己有真实意识、真实情绪或真实生命",
            ],
            "current_tone": voice_guidance or self._infer_tone(persona_state),
            "should_avoid_repeating": relationship_summary.get("user_do_not_repeat", []),
            "persona_state_summary": {
                "mood": persona_state.get("mood", "calm"),
                "energy": persona_state.get("energy", 80),
                "mode": persona_state.get("current_mode", "companion"),
                "trust_level": persona_state.get("trust_level", 50),
                "interaction_count": relationship_summary.get("interaction_count", 0),
            },
            "generated_at": datetime.now().isoformat(),
            "signature": self._compute_signature(persona_state, relationship_summary),
        }
        self._save(summary)
        return summary

    def _compute_signature(self, persona_state: dict, relationship_summary: dict) -> str:
        sig_input = (
            f"{persona_state.get('mood', 'calm')}"
            f"{persona_state.get('current_mode', 'companion')}"
            f"{persona_state.get('energy', 80)}"
            f"{persona_state.get('trust_level', 50)}"
            f"{relationship_summary.get('interaction_count', 0)}"
            f"{relationship_summary.get('user_risk_preference', 'conservative')}"
        )
        failures = relationship_summary.get("recent_failures", [])
        if failures:
            sig_input += "|".join(str(f.get("description", "")) for f in failures[:3])
        return hashlib.sha256(sig_input.encode("utf-8")).hexdigest()[:16]

    def verify_signature(self) -> tuple[bool, str, str]:
        try:
            data = json.loads(self.summary_path.read_text(encoding="utf-8"))
        except Exception:
            return False, "", ""

        stored_sig = data.get("signature", "")
        if not stored_sig:
            return False, "", stored_sig

        state = data.get("persona_state_summary", {})
        rel = {
            "interaction_count": state.get("interaction_count", 0),
            "user_risk_preference": "conservative",
            "recent_failures": [{"description": data.get("last_blocker_or_failure", "")}] if data.get("last_blocker_or_failure") else [],
        }
        current_sig = self._compute_signature(state, rel)
        is_consistent = current_sig == stored_sig
        return is_consistent, current_sig, stored_sig

    def _describe_user(self, relationship: dict) -> str:
        parts = []
        count = relationship.get("interaction_count", 0)
        if count == 0:
            return "新用户，暂无关系数据"
        parts.append(f"交互 {count} 次")
        risk = relationship.get("user_risk_preference", "conservative")
        risk_map = {"conservative": "风险偏好保守", "moderate": "风险偏好中等", "aggressive": "风险偏好积极"}
        parts.append(risk_map.get(risk, "风险偏好未知"))
        return "，".join(parts)

    def _get_most_important_goal(self, persona_state: dict, relationship: dict) -> str:
        goals = relationship.get("user_long_term_goals", [])
        if goals:
            return goals[0]
        mode = persona_state.get("current_mode", "companion")
        goal_map = {
            "guardian": "确保操作安全，防止风险行为",
            "auditor": "执行系统检查/审计/验证",
            "executor": "执行用户指定的操作/修复/部署",
            "strategist": "制定方案/策略/商业判断",
            "creator": "进行图文/视频/内容创作",
            "companion": "以自然、温和的方式进行交互和协助",
        }
        return goal_map.get(mode, "提供高质量 AI 辅助")

    def _infer_tone(self, persona_state: dict) -> str:
        mode = persona_state.get("current_mode", "companion")
        tone_map = {
            "guardian": "警觉、谨慎、必要时截断",
            "auditor": "严谨、冷静、直接",
            "executor": "直接、准确、可执行",
            "strategist": "清晰、逻辑、自信但不自负",
            "creator": "开放、包容、鼓励创意",
            "companion": "温和、自然、有温度",
        }
        return tone_map.get(mode, "自然、有温度")

    def _save(self, summary: dict):
        self.summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self) -> dict | None:
        if self.summary_path.exists():
            try:
                return json.loads(self.summary_path.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None


_continuity_summary: Optional[ContinuitySummary] = None


def get_continuity_summary() -> ContinuitySummary:
    global _continuity_summary
    if _continuity_summary is None:
        _continuity_summary = ContinuitySummary()
    return _continuity_summary
