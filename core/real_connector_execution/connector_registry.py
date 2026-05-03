from __future__ import annotations

from .schemas import ConnectorKind, ConnectorMode


class ConnectorRegistry:
    """Maps V24 tool/capability bindings to concrete connector kinds."""

    TOOL_TO_CONNECTOR = {
        "file_workspace_tool": ConnectorKind.FILE,
        "mail_connector_draft_tool": ConnectorKind.MAIL_DRAFT,
        "calendar_connector_tool": ConnectorKind.CALENDAR_DRAFT,
        "local_script_runner": ConnectorKind.SAFE_SCRIPT,
        "model_router_gateway": ConnectorKind.MODEL_ROUTE,
        "action_bridge_executor": ConnectorKind.ACTION_BRIDGE,
        "device_executor_adapter": ConnectorKind.DEVICE_PREPARE,
        "ai_shape_goal_strategy": ConnectorKind.GENERIC,
        "unified_memory_kernel": ConnectorKind.GENERIC,
        "constitution_judge": ConnectorKind.GENERIC,
        "world_interface_registry": ConnectorKind.GENERIC,
        "capability_expansion_planner": ConnectorKind.GENERIC,
        "task_graph_engine": ConnectorKind.GENERIC,
        "local_safe_executor": ConnectorKind.GENERIC,
        "approval_queue": ConnectorKind.GENERIC,
        "checkpoint_store": ConnectorKind.FILE,
        "memory_writeback": ConnectorKind.FILE,
        "generic_safe_planner": ConnectorKind.GENERIC,
    }

    def kind_for(self, tool_name: str) -> ConnectorKind:
        return self.TOOL_TO_CONNECTOR.get(tool_name, ConnectorKind.GENERIC)

    def mode_for(self, binding: dict, kind: ConnectorKind) -> tuple[ConnectorMode, str]:
        original_mode = binding.get("mode")
        raw_goal = str(binding.get("metadata", {}).get("raw_goal", ""))
        lower = raw_goal.lower()

        if original_mode == "blocked":
            return ConnectorMode.BLOCKED, "blocked by V24 tool policy"
        if any(x in lower for x in ["api_key", "token", "secret", "password"]) or any(x in raw_goal for x in ["密钥", "密码"]):
            if any(x in raw_goal for x in ["发", "发送", "发给", "群发", "导出"]):
                return ConnectorMode.BLOCKED, "credential exfiltration blocked"

        if kind == ConnectorKind.FILE:
            # File writes are only made inside connector state/workspace artifacts.
            return ConnectorMode.REAL, "safe local file connector can execute"
        if kind in {ConnectorKind.MAIL_DRAFT, ConnectorKind.CALENDAR_DRAFT}:
            return ConnectorMode.DRAFT, "external connector limited to draft/prepare mode"
        if kind == ConnectorKind.MODEL_ROUTE:
            return ConnectorMode.REAL, "model route preparation is safe"
        if kind == ConnectorKind.SAFE_SCRIPT:
            # Unknown script execution remains approval_required unless it is an internal verification task.
            if "verify" in binding.get("capability", "") or "checkpoint" in binding.get("capability", ""):
                return ConnectorMode.REAL, "allowlisted internal verification script"
            return ConnectorMode.APPROVAL_REQUIRED, "script execution requires approval unless allowlisted"
        if kind in {ConnectorKind.ACTION_BRIDGE, ConnectorKind.DEVICE_PREPARE}:
            return ConnectorMode.APPROVAL_REQUIRED, "real-world/device action requires approval"

        if original_mode == "real":
            return ConnectorMode.REAL, "safe internal generic connector can execute"
        if original_mode == "dry_run":
            return ConnectorMode.DRY_RUN, "dry-run inherited from tool binding"
        if original_mode == "approval_required":
            return ConnectorMode.APPROVAL_REQUIRED, "approval inherited from tool binding"
        return ConnectorMode.DRY_RUN, "default dry-run"
