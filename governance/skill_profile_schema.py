#!/usr/bin/env python3
"""V106.4 Skill Profile Schema — 定义技能画像的数据结构。"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class SkillProfile:
    skill_id: str                          # 唯一ID
    name: str                              # 可读名称
    description: str                       # 简要描述
    domain_tags: List[str] = field(default_factory=list)       # 领域标签
    task_intents: List[str] = field(default_factory=list)      # 任务意图
    input_types: List[str] = field(default_factory=list)       # 输入类型
    output_types: List[str] = field(default_factory=list)      # 输出类型
    risk_class: str = "low"                # low / medium / high / commit
    external_dependency: bool = False      # 是否需要外部API
    execution_mode: str = "direct"         # direct / mock_only / approval_required / blocked
    context_triggers: List[str] = field(default_factory=list)
    proactive_scenario: str = ""
    specificity_score: float = 0.5         # 0~1 专用度
    generic_score: float = 0.5             # 0~1 泛用度（通用助手类）
    confidence: str = "high"               # high / medium / low
    needs_review: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> SkillProfile:
        return cls(
            skill_id=d.get("skill_id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            domain_tags=d.get("domain_tags", []),
            task_intents=d.get("task_intents", []),
            input_types=d.get("input_types", []),
            output_types=d.get("output_types", []),
            risk_class=d.get("risk_class", "low"),
            external_dependency=bool(d.get("external_dependency", False)),
            execution_mode=d.get("execution_mode", "direct"),
            context_triggers=d.get("context_triggers", []),
            proactive_scenario=d.get("proactive_scenario", ""),
            specificity_score=float(d.get("specificity_score", 0.5)),
            generic_score=float(d.get("generic_score", 0.5)),
            confidence=d.get("confidence", "high"),
            needs_review=bool(d.get("needs_review", False)),
        )
