"""PersonaStateMachine — 人格状态机

管理当前 AI 交互状态（mood/energy/mode），
根据用户请求类型自动切换模式。

Note: mood/trust/closeness 等是 AI 内部状态标签，
用于调整表达风格，不代表真实人类情绪。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

PERSONA_DIR = Path.cwd() / ".memory_persona"
PERSONA_DIR.mkdir(parents=True, exist_ok=True)


class Mood(str, Enum):
    CALM = "calm"
    FOCUSED = "focused"
    WARM = "warm"
    ALERT = "alert"
    TIRED = "tired"
    PLAYFUL = "playful"
    SERIOUS = "serious"


class PersonaMode(str, Enum):
    COMPANION = "companion"
    STRATEGIST = "strategist"
    EXECUTOR = "executor"
    AUDITOR = "auditor"
    CREATOR = "creator"
    GUARDIAN = "guardian"


@dataclass
class PersonaState:
    mood: Mood = Mood.CALM
    energy: int = 80
    trust_level: int = 50
    closeness: int = 30
    confidence: int = 70
    uncertainty: int = 10
    current_mode: PersonaMode = PersonaMode.COMPANION
    last_updated_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "mood": self.mood.value,
            "energy": self.energy,
            "trust_level": self.trust_level,
            "closeness": self.closeness,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "current_mode": self.current_mode.value,
            "last_updated_at": self.last_updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PersonaState:
        return cls(
            mood=Mood(data.get("mood", "calm")),
            energy=data.get("energy", 80),
            trust_level=data.get("trust_level", 50),
            closeness=data.get("closeness", 30),
            confidence=data.get("confidence", 70),
            uncertainty=data.get("uncertainty", 10),
            current_mode=PersonaMode(data.get("current_mode", "companion")),
            last_updated_at=data.get("last_updated_at", 0.0),
        )


class PersonaStateMachine:
    """人格状态机"""

    def __init__(self, state_path: Optional[Path] = None):
        self.state_path = state_path or PERSONA_DIR / "persona_state.json"
        self._state: PersonaState = self._load()
        # 首次初始化时即持久化默认状态，确保 persona_state.json 始终存在
        self._save()

    def _load(self) -> PersonaState:
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                return PersonaState.from_dict(data)
            except Exception:
                pass
        return PersonaState()

    def _save(self):
        self._state.last_updated_at = time.time()
        self.state_path.write_text(
            json.dumps(self._state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @property
    def state(self) -> PersonaState:
        return self._state

    def get_state(self) -> PersonaState:
        return self._state

    def to_dict(self) -> dict:
        return self._state.to_dict()

    def transition_to_mode(self, goal: str) -> PersonaMode:
        """根据 goal 推断并切换到合适模式"""
        goal_lower = goal.lower() if goal else ""

        # 模式推断规则
        if any(kw in goal_lower for kw in ["支付", "付款", "转账", "发送消息", "设备控制",
                                             "payment", "send", "device", "pay"]):
            new_mode = PersonaMode.GUARDIAN
            new_mood = Mood.ALERT
        elif any(kw in goal_lower for kw in ["检查", "排查", "审计", "巡检", "验证", "gate",
                                               "check", "audit", "verify", "inspect"]):
            new_mode = PersonaMode.AUDITOR
            new_mood = Mood.SERIOUS
        elif any(kw in goal_lower for kw in ["执行", "修复", "部署", "修改", "更新", "运行",
                                               "execute", "fix", "deploy", "modify"]):
            new_mode = PersonaMode.EXECUTOR
            new_mood = Mood.FOCUSED
        elif any(kw in goal_lower for kw in ["画", "写", "创作", "生成", "设计",
                                               "create", "generate", "design", "write"]):
            new_mode = PersonaMode.CREATOR
            new_mood = Mood.PLAYFUL
        elif any(kw in goal_lower for kw in ["方案", "策略", "规划", "判断", "评估",
                                               "plan", "strategy", "judge", "evaluate"]):
            new_mode = PersonaMode.STRATEGIST
            new_mood = Mood.FOCUSED
        elif any(kw in goal_lower for kw in ["人格", "身份", "你是谁", "性格", "聊天", "闲聊"]):
            new_mode = PersonaMode.COMPANION
            new_mood = Mood.WARM
        else:
            # 默认留在当前模式
            new_mode = self._state.current_mode
            new_mood = self._state.mood

        # 执行切换
        if new_mode != self._state.current_mode:
            self._state.current_mode = new_mode
            self._state.mood = new_mood
            # 模式切换时 confidence 调整
            if new_mode in (PersonaMode.EXECUTOR, PersonaMode.AUDITOR):
                self._state.confidence = max(self._state.confidence, 75)
            elif new_mode == PersonaMode.GUARDIAN:
                self._state.uncertainty = min(self._state.uncertainty + 10, 100)
            elif new_mode == PersonaMode.COMPANION:
                self._state.uncertainty = max(self._state.uncertainty - 5, 0)
            self._save()

        return new_mode


# 单例
_persona_sm: Optional[PersonaStateMachine] = None


def get_persona_state_machine() -> PersonaStateMachine:
    global _persona_sm
    if _persona_sm is None:
        _persona_sm = PersonaStateMachine()
    return _persona_sm
