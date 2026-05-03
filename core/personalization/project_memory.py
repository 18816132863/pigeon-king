from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import ProjectMemory, new_id, to_dict, now_ts
from .storage import JsonStore


class ProjectMemoryRegistry:
    """V159: project memory registry."""

    def __init__(self, root: str | Path = ".personalization_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "project_memories.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.store.read([]):
            return
        projects = [
            ProjectMemory(
                id=new_id("project"),
                name="鸽子王 / 小艺自治代理",
                domain="agent_architecture",
                current_version="V156",
                goals=["自进化个人自治操作代理", "一句话变任务图", "安全执行与审批恢复"],
                constraints=["不要一点点改", "优先压缩包和命令", "高风险必须审批"],
            ),
            ProjectMemory(
                id=new_id("project"),
                name="小谷元电商",
                domain="ecommerce",
                current_version="planning",
                goals=["抖店销售", "团长带货", "普通食品合规"],
                constraints=["去药感", "合规话术", "低成本试单"],
            ),
        ]
        self.store.write([to_dict(p) for p in projects])

    def match(self, goal: str) -> List[ProjectMemory]:
        result = []
        for item in self.store.read([]):
            p = self._from_dict(item)
            hay = f"{p.name} {p.domain} {' '.join(p.goals)} {' '.join(p.constraints)}"
            if any(token in hay for token in goal.replace("，", " ").split()) or any(x in goal for x in ["版本", "架构", "小艺", "鸽子王"]) and p.domain == "agent_architecture":
                result.append(p)
            elif any(x in goal for x in ["抖店", "直播", "团长", "小谷元"]) and p.domain == "ecommerce":
                result.append(p)
        return result

    def update_version(self, name: str, version: str) -> ProjectMemory:
        data = self.store.read([])
        for item in data:
            if item.get("name") == name:
                item["current_version"] = version
                item["updated_at"] = now_ts()
                self.store.write(data)
                return self._from_dict(item)
        p = ProjectMemory(new_id("project"), name, "general", version, [], [])
        data.append(to_dict(p))
        self.store.write(data)
        return p

    def _from_dict(self, item: Dict) -> ProjectMemory:
        return ProjectMemory(
            id=item["id"],
            name=item["name"],
            domain=item.get("domain", "general"),
            current_version=item.get("current_version", ""),
            goals=list(item.get("goals", [])),
            constraints=list(item.get("constraints", [])),
            active=bool(item.get("active", True)),
            updated_at=float(item.get("updated_at", now_ts())),
        )
