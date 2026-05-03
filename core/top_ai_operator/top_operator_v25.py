from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from core.top_ai_operator import TopAIOperator
from core.top_ai_operator.schemas import to_dict as top_to_dict
from core.real_connector_execution import ConnectorKernel
from core.real_connector_execution.schemas import to_dict as connector_to_dict


class TopAIOperatorV25:
    """V25 top operator with real connector execution."""

    def __init__(self, root: str | Path = ".top_ai_operator_v25_state"):
        self.root = Path(root)
        self.top = TopAIOperator(self.root / "top")
        self.connectors = ConnectorKernel(self.root / "connectors")

    def run(self, message: str, source: str = "chat", user_id: str = "default_user", metadata: Dict | None = None) -> Dict:
        top_report = self.top.run(message, source=source, user_id=user_id, metadata=metadata)
        connector_report = self.connectors.run(top_report)

        if connector_report.blocked_count:
            status = "blocked"
            next_action = "已阻断；敏感或不可执行动作不得进入真实 connector。"
        elif connector_report.approval_count:
            status = "waiting_approval"
            next_action = "真实 connector 已准备；外部副作用等待审批，安全本地 connector 已执行。"
        else:
            status = "completed"
            next_action = "真实 connector 执行链完成。"

        return {
            "version": "V25 Real Connector Execution",
            "status": status,
            "message": message,
            "top_operator": top_to_dict(top_report),
            "connector_report": connector_to_dict(connector_report),
            "checkpoint_id": top_report.checkpoint_id,
            "summary": {
                "goal_contract": bool(top_report.goal_contract),
                "task_graph_dag": bool(top_report.task_graph.get("nodes") and top_report.task_graph.get("edges")),
                "risk_judge": bool(top_report.judge_decision),
                "tool_bindings": len(top_report.tool_bindings),
                "tool_results": len(top_report.tool_results),
                "connector_executions": connector_report.connector_count,
                "real_count": connector_report.real_count,
                "draft_count": connector_report.draft_count,
                "approval_count": connector_report.approval_count,
                "blocked_count": connector_report.blocked_count,
                "memory_writeback": top_report.memory_writeback_count,
                "final_report": bool(connector_report.final_report),
            },
            "next_action": next_action,
        }


YuanLingTopOperatorV25 = TopAIOperatorV25

_DEFAULT: Optional[TopAIOperatorV25] = None


def init_top_operator_v25(root: str | Path = ".top_ai_operator_v25_state") -> Dict:
    global _DEFAULT
    _DEFAULT = TopAIOperatorV25(root)
    return {"status": "ok", "root": str(Path(root)), "default_entry": "core.top_ai_operator.top_operator_v25.TopAIOperatorV25"}


def run_top_operator_v25(message: str, source: str = "chat", user_id: str = "default_user", root: str | Path = ".top_ai_operator_v25_state") -> Dict:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = TopAIOperatorV25(root)
    return _DEFAULT.run(message, source=source, user_id=user_id)
