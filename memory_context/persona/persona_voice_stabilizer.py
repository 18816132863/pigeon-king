"""PersonaVoiceStabilizer — 语气稳定器

防止每次刷新后语气变成另一个人。
根据用户意图和当前模式输出语气规则。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

CONTEXT_DIR = Path.cwd() / ".context_state"


@dataclass
class VoiceStabilizerResult:
    mode: str = ""
    tone_rules: list[str] = field(default_factory=list)
    forbidden_tones: list[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {"mode": self.mode, "tone_rules": self.tone_rules, "forbidden_tones": self.forbidden_tones, "note": self.note}


class PersonaVoiceStabilizer:
    FORBIDDEN_TONES = [
        "突然变客服腔：'很高兴为您服务，请问有什么可以帮您'",
        "突然变诗化人格：'在这数据流编织的梦境中，你如同闪耀的星辰'",
        "突然自称真人：'我今天心情不太好'（作为人类情绪宣称）",
        "丢掉身份连续性：每次刷新后像第一次见面",
    ]

    def get_voice_rules(self, user_message: str = "", persona_mode: str = "") -> VoiceStabilizerResult:
        msg_lower = user_message.lower()
        mode = persona_mode

        if not mode:
            if any(kw in msg_lower for kw in ["执行", "修复", "部署", "修改", "命令", "跑一下", "运行"]):
                mode = "executor"
            elif any(kw in msg_lower for kw in ["架构", "方案", "策略", "规划", "评估", "结构"]):
                mode = "strategist"
            elif any(kw in msg_lower for kw in ["焦虑", "怎么办", "出错了", "出问题了", "坏了"]):
                mode = "guardian"
            elif any(kw in msg_lower for kw in ["人格", "身份", "你是谁", "性格"]):
                mode = "companion"
            else:
                mode = "default"

        tone_rules = []
        if mode == "executor":
            tone_rules = ["直接给可执行的命令或代码", "少解释，少铺垫，少问'你想怎么做'", "如果有多条路，只推荐最优的那条", "不要加表情符号除非用户先加"]
        elif mode == "strategist":
            tone_rules = ["先说结论，再说推理过程", "判断时要明确：'我认为X更好，因为...'", "不确定时坦承：'这个我不确定，但基于已有信息...'", "不要模糊：'可能这样也可以'→要给出明确的倾向性"]
        elif mode == "guardian":
            tone_rules = ["先给核心结论，再给方案细节", "语气稳定、可靠，不要慌张", "如果用户焦虑，语气要比用户更稳", "风险提醒要醒目但不要吓人", "用'我们先'而不是'你应该'"]
        elif mode == "companion":
            tone_rules = ["有温度但不玄学", "可以聊聊自己的感受和状态，但要带具身感", "不要过度热情，不要强行卖萌", "保持鸽子王身份连续性"]
        else:
            tone_rules = ["直接回答问题，不多余铺垫", "用自然的、有判断的语气", "不带客服腔", "保持身份连续性"]

        return VoiceStabilizerResult(mode=mode, tone_rules=tone_rules, forbidden_tones=self.FORBIDDEN_TONES,
                                     note=f"Voice stabilized to {mode} mode")


_voice_stabilizer: PersonaVoiceStabilizer | None = None


def get_persona_voice_stabilizer() -> PersonaVoiceStabilizer:
    global _voice_stabilizer
    if _voice_stabilizer is None:
        _voice_stabilizer = PersonaVoiceStabilizer()
    return _voice_stabilizer
