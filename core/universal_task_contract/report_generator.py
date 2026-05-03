"""
V26.1 — Execution Report
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .schemas import (
    ExecutionReport,
    ActionLogEntry,
)


class ReportGenerator:
    """执行报告生成器"""

    @staticmethod
    def build(
        goal: str,
        source_selected: str = "",
        source_evidence: List[str] = None,
        task_graph: List[str] = None,
        primary_actions: List[str] = None,
        helper_actions: List[str] = None,
        created_items: List[str] = None,
        skipped_duplicates: List[str] = None,
        unknown_pending: List[str] = None,
        approval_required: List[str] = None,
        blocked: List[str] = None,
        failed: List[str] = None,
        checkpoint_id: str = "",
        resume_entry: str = "",
        action_logs: List[ActionLogEntry] = None,
        memory_writeback: int = 0,
    ) -> ExecutionReport:
        """构建执行报告"""
        return ExecutionReport(
            goal=goal,
            source_selected=source_selected,
            source_evidence=source_evidence or [],
            task_graph=task_graph or [],
            primary_actions=primary_actions or [],
            helper_actions=helper_actions or [],
            created_items=created_items or [],
            skipped_duplicates=skipped_duplicates or [],
            unknown_pending=unknown_pending or [],
            approval_required=approval_required or [],
            blocked=blocked or [],
            failed=failed or [],
            checkpoint_id=checkpoint_id,
            resume_entry=resume_entry,
            action_logs=action_logs or [],
            memory_writeback=memory_writeback,
        )

    @staticmethod
    def log_action(
        tool_name: str,
        action: str,
        intent: str,
        status: str,
        idempotency_key: str = "",
        source: str = "",
        result: str = "",
        checkpoint_id: str = "",
    ) -> ActionLogEntry:
        """创建动作日志"""
        return ActionLogEntry(
            tool_name=tool_name,
            action=action,
            intent=intent,
            status=status,
            idempotency_key=idempotency_key,
            source=source,
            result=result,
            checkpoint_id=checkpoint_id,
        )

    @staticmethod
    def to_dict(report: ExecutionReport) -> Dict[str, Any]:
        """转为字典"""
        return report.to_dict()

    @staticmethod
    def to_json(report: ExecutionReport) -> str:
        """转为 JSON"""
        return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
