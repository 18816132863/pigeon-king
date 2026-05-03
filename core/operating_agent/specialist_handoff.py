from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .schemas import SpecialistAgent, HandoffRecord, new_id, dataclass_to_dict
from .storage import JsonStore


class SpecialistHandoffManager:
    """V102: specialist agent handoff manager."""

    def __init__(self, root: str | Path = ".operating_agent_state"):
        self.root = Path(root)
        self.agent_store = JsonStore(self.root / "specialist_agents.json")
        self.handoff_store = JsonStore(self.root / "handoff_records.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.agent_store.read([]):
            return
        agents = [
            SpecialistAgent(new_id("agent"), "Architecture Specialist", ["architecture", "system", "模块", "架构"], "reasoning_high", ["code_review"], priority=90),
            SpecialistAgent(new_id("agent"), "Commerce Specialist", ["电商", "直播", "抖店", "话术"], "chinese_business", ["market_research"], priority=80),
            SpecialistAgent(new_id("agent"), "Compliance Specialist", ["规则", "合规", "资质", "风险"], "reasoning_high", ["web_search"], priority=85),
            SpecialistAgent(new_id("agent"), "Media Specialist", ["图片", "视频", "海报", "logo"], "multimodal_generation", ["image_generation", "video_generation"], priority=75),
            SpecialistAgent(new_id("agent"), "Code Specialist", ["代码", "pytest", "报错", "接口"], "coding_high", ["repo_edit"], priority=88),
        ]
        self.agent_store.write([dataclass_to_dict(a) for a in agents])

    def choose(self, goal: str) -> SpecialistAgent:
        candidates = []
        for item in self.agent_store.read([]):
            agent = self._agent_from_dict(item)
            score = agent.priority
            for domain in agent.domains:
                if domain.lower() in goal.lower():
                    score += 50
            candidates.append((score, agent))
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def create_handoff(self, goal: str, from_agent: str, reason: str, payload: Dict) -> HandoffRecord:
        to_agent = self.choose(goal)
        record = HandoffRecord(
            id=new_id("handoff"),
            goal=goal,
            from_agent=from_agent,
            to_agent=to_agent.name,
            reason=reason,
            payload=payload,
        )
        self.handoff_store.append(dataclass_to_dict(record))
        return record

    def records(self) -> List[HandoffRecord]:
        return [self._handoff_from_dict(x) for x in self.handoff_store.read([])]

    def _agent_from_dict(self, item: Dict) -> SpecialistAgent:
        return SpecialistAgent(
            id=item["id"],
            name=item["name"],
            domains=list(item.get("domains", [])),
            model_group=item.get("model_group", "reasoning_high"),
            tools=list(item.get("tools", [])),
            priority=int(item.get("priority", 50)),
        )

    def _handoff_from_dict(self, item: Dict) -> HandoffRecord:
        return HandoffRecord(
            id=item["id"],
            goal=item["goal"],
            from_agent=item["from_agent"],
            to_agent=item["to_agent"],
            reason=item["reason"],
            payload=dict(item.get("payload", {})),
            status=item.get("status", "created"),
            created_at=float(item.get("created_at", 0.0)),
        )
