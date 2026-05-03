from __future__ import annotations

from pathlib import Path

from .schemas import ConnectorExecution, ConnectorKind, ConnectorMode, ConnectorStatus, new_id, to_dict
from .storage import JsonStore
from .connector_registry import ConnectorRegistry
from .connectors import (
    FileWorkspaceConnector,
    MailDraftConnector,
    CalendarDraftConnector,
    SafeScriptConnector,
    ModelRouteConnector,
    ActionBridgeConnector,
    DevicePrepareConnector,
    GenericConnector,
)


class ConnectorExecutor:
    """Executes connector actions based on tool bindings."""

    def __init__(self, root: str | Path = ".real_connector_execution_state"):
        self.root = Path(root)
        self.registry = ConnectorRegistry()
        self.store = JsonStore(self.root / "connector_executions.json")
        self.connectors = {
            ConnectorKind.FILE: FileWorkspaceConnector(self.root),
            ConnectorKind.MAIL_DRAFT: MailDraftConnector(self.root),
            ConnectorKind.CALENDAR_DRAFT: CalendarDraftConnector(self.root),
            ConnectorKind.SAFE_SCRIPT: SafeScriptConnector(self.root),
            ConnectorKind.MODEL_ROUTE: ModelRouteConnector(self.root),
            ConnectorKind.ACTION_BRIDGE: ActionBridgeConnector(self.root),
            ConnectorKind.DEVICE_PREPARE: DevicePrepareConnector(self.root),
            ConnectorKind.GENERIC: GenericConnector(self.root),
        }

    def execute_binding(self, top_report_id: str, binding: dict) -> ConnectorExecution:
        kind = self.registry.kind_for(binding.get("tool_name", ""))
        mode, reason = self.registry.mode_for(binding, kind)

        if mode == ConnectorMode.BLOCKED:
            status, output, error = ConnectorStatus.BLOCKED, {"blocked": True, "reason": reason}, ""
        elif mode == ConnectorMode.APPROVAL_REQUIRED:
            status, output, error = ConnectorStatus.WAITING_APPROVAL, {"approval_required": True, "reason": reason}, ""
        else:
            status, output, error = self.connectors[kind].execute(binding, mode)
            output["mode_reason"] = reason

        execution = ConnectorExecution(
            id=new_id("connector_exec"),
            top_report_id=top_report_id,
            tool_binding_id=binding.get("id", ""),
            task_id=binding.get("task_id", ""),
            task_title=binding.get("task_title", ""),
            tool_name=binding.get("tool_name", ""),
            capability=binding.get("capability", ""),
            connector_kind=kind,
            mode=mode,
            status=status,
            checkpoint_id=binding.get("checkpoint_id", ""),
            output=output,
            error=error,
        )
        self.store.append(to_dict(execution))
        return execution
