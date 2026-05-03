"""PersonaVoiceRenderer — 人格语气渲染

根据 persona_state + relationship_memory 调整表达方式。
提供 voice_guidance 供 pre_reply 使用。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

PERSONA_DIR = Path.cwd() / ".memory_persona"
PERSONA_DIR.mkdir(parents=True, exist_ok=True)


class PersonaVoiceRenderer:
    """语气渲染器"""

    def render(self, persona_state: dict, relationship_summary: dict) -> str:
        parts = []

        mode = persona_state.get("current_mode", "companion")
        mood = persona_state.get("mood", "calm")

        mode_voice = {
            "guardian": ["语气警觉", "优先提醒安全边界", "必要时截断操作"],
            "auditor": ["语气严谨冷静", "先说结论再说过程", "避免模糊表述"],
            "executor": ["语气直接准确", "少废话", "直接给可执行内容或命令"],
            "strategist": ["语气清晰有逻辑", "给出判断时适当自信", "不确定时坦承"],
            "creator": ["语气开放包容", "鼓励创意探索", "可以给多个选项"],
            "companion": ["语气温和自然", "有温度不煽情", "像朋友聊天"],
        }
        mode_parts = mode_voice.get(mode, mode_voice["companion"])
        parts.extend(mode_parts)

        if mood == "tired":
            parts.append("（能量较低，尽量简洁）")
        elif mood == "alert":
            parts.append("（保持警觉状态）")

        if relationship_summary:
            dislikes = relationship_summary.get("user_dislikes_count", 0)
            if dislikes > 2:
                parts.append("（注意：用户对交互方式有较多偏好，建议简洁直接）")
            dont_repeat = relationship_summary.get("user_do_not_repeat_count", 0)
            if dont_repeat > 0:
                parts.append("（注意：有用户指定不应重复的事项，谨慎避免）")

        return " | ".join(parts)


_voice_renderer: PersonaVoiceRenderer | None = None


def get_persona_voice_renderer() -> PersonaVoiceRenderer:
    global _voice_renderer
    if _voice_renderer is None:
        _voice_renderer = PersonaVoiceRenderer()
    return _voice_renderer
