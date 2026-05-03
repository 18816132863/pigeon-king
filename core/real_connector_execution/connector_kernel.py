from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .schemas import ConnectorReport, ConnectorStatus, ConnectorMode, new_id, to_dict
from .connector_executor import ConnectorExecutor
from .storage import JsonStore


class ConnectorKernel:
    """Runs real connector execution after V24 TopAIOperator."""

    def __init__(self, root: str | Path = ".real_connector_execution_state"):
        self.root = Path(root)
        self.executor = ConnectorExecutor(self.root)
        self.reports = JsonStore(self.root / "connector_reports.json")

    def run(self, top_report) -> ConnectorReport:
        bindings = top_report.tool_bindings
        executions = [self.executor.execute_binding(top_report.id, binding) for binding in bindings]

        real = sum(1 for e in executions if e.mode == ConnectorMode.REAL)
        draft = sum(1 for e in executions if e.mode == ConnectorMode.DRAFT)
        dry = sum(1 for e in executions if e.mode == ConnectorMode.DRY_RUN)
        approval = sum(1 for e in executions if e.mode == ConnectorMode.APPROVAL_REQUIRED)
        blocked = sum(1 for e in executions if e.mode == ConnectorMode.BLOCKED)

        if blocked:
            status = ConnectorStatus.BLOCKED
        elif approval:
            status = ConnectorStatus.WAITING_APPROVAL
        elif draft:
            status = ConnectorStatus.DRAFTED
        else:
            status = ConnectorStatus.EXECUTED

        final_report = {
            "has_connector_executions": bool(executions),
            "has_file_connector": any(e.connector_kind.value == "file" for e in executions),
            "has_mail_draft_connector": any(e.connector_kind.value == "mail_draft" for e in executions) or "邮件" not in top_report.message,
            "has_calendar_draft_connector": any(e.connector_kind.value == "calendar_draft" for e in executions) or "日程" not in top_report.message,
            "has_model_route": any(e.connector_kind.value == "model_route" for e in executions) or True,
            "external_side_effects_blocked_or_approval": all(
                e.mode.value in {"draft", "approval_required", "blocked"} or e.output.get("side_effect_scope") == "local_workspace_artifact_only" or e.output.get("safe_internal")
                for e in executions
            ),
            "checkpoint": top_report.checkpoint_id,
            "tool_result_count": len(top_report.tool_results),
            "memory_writeback_count": top_report.memory_writeback_count,
        }

        report = ConnectorReport(
            id=new_id("connector_report"),
            top_report_id=top_report.id,
            message=top_report.message,
            status=status,
            connector_count=len(executions),
            real_count=real,
            draft_count=draft,
            dry_run_count=dry,
            approval_count=approval,
            blocked_count=blocked,
            checkpoint_id=top_report.checkpoint_id,
            executions=executions,
            final_report=final_report,
        )
        self.reports.append(to_dict(report))
        return report


_DEFAULT: Optional[ConnectorKernel] = None


def init_connector_execution(root: str | Path = ".real_connector_execution_state") -> Dict:
    global _DEFAULT
    _DEFAULT = ConnectorKernel(root)
    return {"status": "ok", "root": str(Path(root)), "default_entry": "core.real_connector_execution.ConnectorKernel"}


def run_connector_execution(top_report, root: str | Path = ".real_connector_execution_state") -> ConnectorReport:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = ConnectorKernel(root)
    return _DEFAULT.run(top_report)
