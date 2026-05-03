from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from core.top_ai_operator.top_operator_v25 import TopAIOperatorV25
from .supervisor import TimeoutResilienceSupervisor
from .schemas import to_dict


class TopAIOperatorV26:
    """V26 top operator with timeout resilience supervisor."""

    def __init__(self, root: str | Path = ".top_ai_operator_v26_state"):
        self.root = Path(root)
        self.v25 = TopAIOperatorV25(self.root / "v25")
        self.timeout = TimeoutResilienceSupervisor(self.root / "timeout_resilience")

    def run(self, message: str, source: str = "chat", user_id: str = "default_user", metadata: Dict | None = None) -> Dict:
        metadata = metadata or {}
        estimated_seconds = int(metadata.get("estimated_seconds", 120 if self._looks_long_or_device(message) else 20))
        approved = bool(metadata.get("approved", False))

        top = self.v25.run(message, source=source, user_id=user_id, metadata=metadata)
        timeout_report = self.timeout.run(message, estimated_seconds=estimated_seconds, approved=approved)

        if timeout_report.status.value == "waiting_approval":
            status = "waiting_approval"
            next_action = "端侧/外部工具已转为非阻塞审批等待；不会再卡死 60 秒。"
        elif timeout_report.status.value in {"resumable", "paused_before_timeout", "heartbeat_ok"}:
            status = "resumable"
            next_action = "长任务已拆分并写入 checkpoint，可轮询/恢复，不再单次阻塞超时。"
        elif top["status"] == "blocked":
            status = "blocked"
            next_action = "请求被安全策略阻断。"
        else:
            status = top["status"]
            next_action = "V26 超时治理链完成。"

        return {
            "version": "V26 Timeout Resilience",
            "status": status,
            "message": message,
            "top_operator_v25": top,
            "timeout_resilience": to_dict(timeout_report),
            "checkpoint_id": timeout_report.checkpoint_id,
            "summary": {
                "default_entry": "TopAIOperatorV26",
                "v25_status": top["status"],
                "timeout_status": timeout_report.status.value,
                "estimated_seconds": estimated_seconds,
                "step_count": len(timeout_report.job.steps),
                "heartbeat_count": len(timeout_report.heartbeats),
                "checkpoint": bool(timeout_report.checkpoint_id),
                "resumable": timeout_report.status.value in {"resumable", "paused_before_timeout", "heartbeat_ok", "waiting_approval"},
                "no_blocking_call_over_soft_deadline": timeout_report.no_blocking_call_over_soft_deadline,
                "approval_required": timeout_report.job.approval_required,
                "memory_writeback": top["summary"]["memory_writeback"],
                "connector_executions": top["summary"]["connector_executions"],
            },
            "next_action": next_action,
        }

    def _looks_long_or_device(self, message: str) -> bool:
        return any(x in message for x in ["端侧", "设备", "手机", "Calendar", "日程", "大量", "批量", "超时", "60秒", "长任务"])


YuanLingTopOperatorV26 = TopAIOperatorV26

_DEFAULT: Optional[TopAIOperatorV26] = None


def init_top_operator_v26(root: str | Path = ".top_ai_operator_v26_state") -> Dict:
    global _DEFAULT
    _DEFAULT = TopAIOperatorV26(root)
    return {"status": "ok", "root": str(Path(root)), "default_entry": "core.device_timeout_resilience.TopAIOperatorV26"}


def run_top_operator_v26(message: str, source: str = "chat", user_id: str = "default_user", root: str | Path = ".top_ai_operator_v26_state", metadata: Dict | None = None) -> Dict:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = TopAIOperatorV26(root)
    return _DEFAULT.run(message, source=source, user_id=user_id, metadata=metadata)
