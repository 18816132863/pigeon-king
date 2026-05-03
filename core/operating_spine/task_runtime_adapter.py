from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import RuntimeNodeResult, RuntimeNodeStatus, new_id, to_dict
from .storage import JsonStore


class TaskRuntimeAdapter:
    """V120: binds goal/task graph semantics to runtime nodes."""

    def __init__(self, root: str | Path = ".operating_spine_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "runtime_node_results.json")

    def compile_nodes(self, goal: str) -> List[Dict]:
        nodes = [
            {"name": "compile_goal", "capability": "personal_execution_agent", "risk": "L1"},
            {"name": "govern_action", "capability": "operating_governance", "risk": "L2"},
            {"name": "self_evolution_check", "capability": "self_evolution_ops", "risk": "L1"},
            {"name": "execute_or_wait", "capability": "autonomy_kernel", "risk": "L2"},
        ]
        if any(x in goal for x in ["发送", "转账", "删除", "安装", "客户", "外部"]):
            nodes.insert(2, {"name": "approval_gate", "capability": "approval_recovery", "risk": "L4"})
        return nodes

    def run_dry(self, goal: str) -> List[RuntimeNodeResult]:
        results = []
        nodes = self.compile_nodes(goal)
        for i, node in enumerate(nodes):
            if node["name"] == "approval_gate":
                status = RuntimeNodeStatus.WAITING_APPROVAL
                summary = "high-risk node requires approval checkpoint"
            else:
                status = RuntimeNodeStatus.READY if i < len(nodes) - 1 else RuntimeNodeStatus.COMPLETED
                summary = "node is routable"
            result = RuntimeNodeResult(
                id=new_id("node"),
                node_name=node["name"],
                status=status,
                selected_capability=node["capability"],
                risk_level=node["risk"],
                output_summary=summary,
                next_nodes=[nodes[i+1]["name"]] if i + 1 < len(nodes) else [],
            )
            results.append(result)
        self.store.write([to_dict(x) for x in results])
        return results
