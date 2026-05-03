from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .specialist_handoff import SpecialistHandoffManager


class MultiAgentCoordinator:
    """V103: multi-specialist coordination and consensus compiler."""

    def __init__(self, root: str | Path = ".operating_agent_state"):
        self.root = Path(root)
        self.handoff = SpecialistHandoffManager(root)

    def decompose_domains(self, goal: str) -> List[str]:
        domains = []
        mapping = {
            "architecture": ["架构", "模块", "系统"],
            "commerce": ["电商", "直播", "抖店", "卖货", "话术"],
            "compliance": ["规则", "合规", "资质", "风险"],
            "media": ["图片", "视频", "logo", "海报"],
            "code": ["代码", "pytest", "报错", "接口"],
        }
        for domain, kws in mapping.items():
            if any(k in goal for k in kws):
                domains.append(domain)
        return domains or ["general"]

    def coordinate(self, goal: str) -> Dict:
        domains = self.decompose_domains(goal)
        handoffs = []
        for domain in domains:
            record = self.handoff.create_handoff(
                goal=goal,
                from_agent="OperatingAgentOrchestrator",
                reason=f"domain_required::{domain}",
                payload={"domain": domain},
            )
            handoffs.append(record)
        consensus = {
            "goal": goal,
            "domains": domains,
            "handoff_agents": [h.to_agent for h in handoffs],
            "consensus_plan": [
                "compile goal",
                "judge constitution",
                "resolve permissions",
                "select connectors",
                "route to specialists",
                "verify result",
            ],
        }
        return consensus
