from __future__ import annotations

class ToolRegistry:
    """Concrete capability/tool slots used by the top AI operator."""

    DEFAULT_TOOLS = {
        "goal_compile": {
            "tool_name": "ai_shape_goal_strategy",
            "capability": "compile_goal_contract",
            "safe_real": True,
        },
        "memory_context": {
            "tool_name": "unified_memory_kernel",
            "capability": "read_personal_memory",
            "safe_real": True,
        },
        "constitution_judge": {
            "tool_name": "constitution_judge",
            "capability": "risk_and_policy_judge",
            "safe_real": True,
        },
        "world_capability_scan": {
            "tool_name": "world_interface_registry",
            "capability": "scan_available_capabilities",
            "safe_real": True,
        },
        "capability_gap": {
            "tool_name": "capability_expansion_planner",
            "capability": "sandbox_expansion_plan",
            "safe_real": False,
        },
        "task_dag": {
            "tool_name": "task_graph_engine",
            "capability": "compile_task_dag",
            "safe_real": True,
        },
        "safe_execution": {
            "tool_name": "local_safe_executor",
            "capability": "execute_local_safe_task",
            "safe_real": True,
        },
        "approval_gate": {
            "tool_name": "approval_queue",
            "capability": "human_approval_checkpoint",
            "safe_real": False,
        },
        "checkpoint_recovery": {
            "tool_name": "checkpoint_store",
            "capability": "write_checkpoint_and_recovery",
            "safe_real": True,
        },
        "completion_memory_writeback": {
            "tool_name": "memory_writeback",
            "capability": "write_memory_and_final_report",
            "safe_real": True,
        },
        "file_operation": {
            "tool_name": "file_workspace_tool",
            "capability": "read_write_workspace_file",
            "safe_real": True,
        },
        "mail_operation": {
            "tool_name": "mail_connector_draft_tool",
            "capability": "draft_or_prepare_email",
            "safe_real": False,
        },
        "calendar_operation": {
            "tool_name": "calendar_connector_tool",
            "capability": "read_or_prepare_calendar_action",
            "safe_real": False,
        },
        "script_operation": {
            "tool_name": "local_script_runner",
            "capability": "run_local_script_dry_or_safe",
            "safe_real": False,
        },
        "model_route": {
            "tool_name": "model_router_gateway",
            "capability": "select_best_model",
            "safe_real": True,
        },
        "action_bridge": {
            "tool_name": "action_bridge_executor",
            "capability": "prepare_real_world_action",
            "safe_real": False,
        },
        "device_operation": {
            "tool_name": "device_executor_adapter",
            "capability": "prepare_device_action",
            "safe_real": False,
        },
    }

    KEYWORD_TO_KIND = [
        (("邮件", "邮箱", "客户", "发送"), "mail_operation"),
        (("日程", "会议", "日历"), "calendar_operation"),
        (("文件", "压缩包", "覆盖", "保存", "替换"), "file_operation"),
        (("脚本", "命令", "运行", "执行"), "script_operation"),
        (("模型", "路由", "API"), "model_route"),
        (("手机", "设备", "点击", "打开应用"), "device_operation"),
    ]

    def lookup(self, task_kind: str, task_title: str = "", goal: str = "") -> dict:
        if task_kind in self.DEFAULT_TOOLS:
            return self.DEFAULT_TOOLS[task_kind]
        hay = f"{task_title} {goal}"
        for keywords, kind in self.KEYWORD_TO_KIND:
            if any(k in hay for k in keywords):
                return self.DEFAULT_TOOLS[kind]
        return {
            "tool_name": "generic_safe_planner",
            "capability": "plan_or_dry_run_generic_task",
            "safe_real": True,
        }
