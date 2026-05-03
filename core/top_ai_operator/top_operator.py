from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from core.ai_shape_core import AIShapeCore
from core.ai_shape_core.schemas import to_dict as ai_to_dict
from core.real_tool_binding import ToolBindingKernel
from core.real_tool_binding.schemas import to_dict as tool_to_dict

from .schemas import TopOperatorReport, TopOperatorStatus, new_id, to_dict
from .storage import JsonStore

class TopAIOperator:
    """Final top-level operator entry.

    It is safe by default and tool-bound by default.
    """

    def __init__(self, root: str | Path = ".top_ai_operator_state"):
        self.root = Path(root)
        self.ai_core = AIShapeCore(self.root / "ai_shape_core")
        self.tool_binding = ToolBindingKernel(self.root / "real_tool_binding")
        self.reports = JsonStore(self.root / "top_operator_reports.json")

    def run(self, message: str, source: str = "chat", user_id: str = "default_user", metadata: Dict | None = None) -> TopOperatorReport:
        ai_result = self.ai_core.run(message)
        tool_report = self.tool_binding.run(ai_result)

        if tool_report.blocked_count or ai_result.blocked_tasks:
            status = TopOperatorStatus.BLOCKED
            next_action = "已阻断；请移除敏感外泄/不可执行动作后重试。"
        elif tool_report.approval_count or ai_result.approval_tasks:
            status = TopOperatorStatus.WAITING_APPROVAL
            next_action = "安全部分已完成；外部副作用/高风险工具等待审批后从 checkpoint 恢复。"
        else:
            status = TopOperatorStatus.COMPLETED
            next_action = "顶层 AI Operator 已完成真实任务入口、工具绑定、工具结果、checkpoint 和记忆回写。"

        final_report = {
            "has_goal_contract": bool(ai_result.goal_contract),
            "has_task_graph_dag": bool(ai_result.task_graph.nodes and ai_result.task_graph.edges),
            "has_risk_judge": bool(ai_result.judge_decision.value),
            "has_tool_bindings": bool(tool_report.bindings),
            "has_tool_results": bool(tool_report.results),
            "has_tool_modes": bool(tool_report.mode_counts),
            "has_auto_executed_tasks": bool(ai_result.auto_executed_tasks),
            "has_approval_tasks": bool(ai_result.approval_tasks) or status != TopOperatorStatus.COMPLETED,
            "has_checkpoint": bool(ai_result.checkpoint_id),
            "has_action_log": bool(tool_report.results),
            "has_memory_writeback": bool(ai_result.memory_writes),
            "has_final_report": True,
        }

        report = TopOperatorReport(
            id=new_id("top_report"),
            message=message,
            status=status,
            final_status=ai_result.final_status,
            goal_contract=ai_to_dict(ai_result.goal_contract),
            task_graph=ai_to_dict(ai_result.task_graph),
            judge_decision=ai_result.judge_decision.value,
            risk_level=ai_result.risk_level.value,
            tool_bindings=[tool_to_dict(x) for x in tool_report.bindings],
            tool_results=[tool_to_dict(x) for x in tool_report.results],
            tool_mode_counts=tool_report.mode_counts,
            auto_executed_tasks=ai_result.auto_executed_tasks,
            approval_tasks=ai_result.approval_tasks,
            blocked_tasks=ai_result.blocked_tasks,
            checkpoint_id=ai_result.checkpoint_id,
            action_log_count=len(tool_report.results),
            memory_writeback_count=len(ai_result.memory_writes),
            final_report=final_report,
            next_action=next_action,
        )
        self.reports.append(to_dict(report))
        return report

YuanLingTopOperator = TopAIOperator

_DEFAULT: Optional[TopAIOperator] = None

def init_top_operator(root: str | Path = ".top_ai_operator_state") -> Dict:
    global _DEFAULT
    _DEFAULT = TopAIOperator(root)
    return {"status": "ok", "root": str(Path(root)), "default_entry": "core.top_ai_operator.TopAIOperator"}

def run_top_operator(message: str, source: str = "chat", user_id: str = "default_user", root: str | Path = ".top_ai_operator_state") -> TopOperatorReport:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = TopAIOperator(root)
    return _DEFAULT.run(message, source=source, user_id=user_id)
