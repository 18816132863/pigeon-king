from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from core.ai_shape_core import AIShapeCore
from core.ai_shape_core.schemas import to_dict as ai_to_dict

from .schemas import RealWorkReport, EntryStatus, new_id, to_dict
from .message_entry import RealWorkMessageEntry
from .action_log import ActionLogStore
from .storage import JsonStore


class RealWorkEntry:
    """V23.2 real-work default entry.

    This should be the default path for all incoming user messages.
    """

    def __init__(self, root: str | Path = ".real_work_entry_state"):
        self.root = Path(root)
        self.messages = RealWorkMessageEntry(self.root)
        self.action_logs = ActionLogStore(self.root)
        self.reports = JsonStore(self.root / "reports.json")
        self.ai_core = AIShapeCore(self.root / "ai_shape_core")

    def run(self, message: str, source: str = "chat", user_id: str = "default_user", metadata: Dict | None = None) -> RealWorkReport:
        request = self.messages.receive(message, source=source, user_id=user_id, metadata=metadata)
        ai_result = self.ai_core.run(request.message)

        log_records = []
        for trace in ai_result.execution_traces:
            log_records.append(self.action_logs.record_from_trace(request.id, ai_result, trace))

        if ai_result.blocked_tasks:
            status = EntryStatus.BLOCKED
            next_action = "请求被法典裁判阻断；需要改写目标或移除敏感/不可执行内容。"
        elif ai_result.approval_tasks:
            status = EntryStatus.WAITING_APPROVAL
            next_action = "安全部分已完成；真实外部副作用等待用户审批后从 checkpoint 恢复。"
        else:
            status = EntryStatus.COMPLETED
            next_action = "真实任务主链已完成；可查看 action_log、memory_writeback 和 final_result_report。"

        final_result_report = {
            "has_goal_contract": bool(ai_result.goal_contract),
            "has_task_graph_dag": bool(ai_result.task_graph.nodes and ai_result.task_graph.edges),
            "has_risk_judge": bool(ai_result.judge_decision.value),
            "has_auto_executed_tasks": bool(ai_result.auto_executed_tasks),
            "has_approval_tasks": bool(ai_result.approval_tasks) or ai_result.final_status.startswith("completed"),
            "has_checkpoint": bool(ai_result.checkpoint_id),
            "has_action_log": bool(log_records),
            "has_memory_writeback": bool(ai_result.memory_writes),
            "has_final_report": True,
            "completion_report": ai_result.completion_report,
        }

        report = RealWorkReport(
            id=new_id("rwreport"),
            request_id=request.id,
            source=request.source,
            status=status,
            final_status=ai_result.final_status,
            goal_contract=ai_to_dict(ai_result.goal_contract),
            task_graph=ai_to_dict(ai_result.task_graph),
            judge_decision=ai_result.judge_decision.value,
            risk_level=ai_result.risk_level.value,
            auto_executed_tasks=ai_result.auto_executed_tasks,
            approval_tasks=ai_result.approval_tasks,
            blocked_tasks=ai_result.blocked_tasks,
            checkpoint_id=ai_result.checkpoint_id,
            action_log_count=len(log_records),
            memory_writeback_count=len(ai_result.memory_writes),
            final_result_report=final_result_report,
            next_action=next_action,
        )
        self.reports.append(to_dict(report))
        return report


YuanLingRealWorkEntry = RealWorkEntry

_DEFAULT: Optional[RealWorkEntry] = None


def init_real_work_entry(root: str | Path = ".real_work_entry_state") -> Dict:
    global _DEFAULT
    _DEFAULT = RealWorkEntry(root)
    return {"status": "ok", "root": str(Path(root)), "default_entry": "core.real_work_entry.RealWorkEntry"}


def run_real_work_entry(message: str, source: str = "chat", user_id: str = "default_user", root: str | Path = ".real_work_entry_state") -> RealWorkReport:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = RealWorkEntry(root)
    return _DEFAULT.run(message, source=source, user_id=user_id)
