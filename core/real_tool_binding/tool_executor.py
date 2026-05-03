from __future__ import annotations

from pathlib import Path
from .schemas import ToolBinding, ToolExecutionResult, ToolBindingStatus, ToolMode, new_id, to_dict
from .storage import JsonStore

class ToolExecutor:
    """Executes bound tools safely.

    REAL here means safe local/internal execution only: writing logs/checkpoints,
    producing reports, reading internal state. External side effects are not
    executed unless a future approved adapter explicitly takes over.
    """

    def __init__(self, root: str | Path = ".real_tool_binding_state"):
        self.root = Path(root)
        self.result_store = JsonStore(self.root / "tool_results.json")
        self.checkpoint_store = JsonStore(self.root / "tool_checkpoints.json")
        self.approval_store = JsonStore(self.root / "approval_queue.json")

    def execute(self, binding: ToolBinding) -> ToolExecutionResult:
        if binding.mode == ToolMode.BLOCKED:
            result = ToolExecutionResult(
                id=new_id("toolresult"),
                binding_id=binding.id,
                task_id=binding.task_id,
                tool_name=binding.tool_name,
                mode=binding.mode,
                status=ToolBindingStatus.BLOCKED,
                output={"blocked": True, "reason": binding.reason, "checkpoint_id": binding.checkpoint_id},
            )
        elif binding.mode == ToolMode.APPROVAL_REQUIRED:
            approval_item = {
                "id": new_id("approval"),
                "binding_id": binding.id,
                "task_title": binding.task_title,
                "tool_name": binding.tool_name,
                "reason": binding.reason,
                "checkpoint_id": binding.checkpoint_id,
            }
            self.approval_store.append(approval_item)
            result = ToolExecutionResult(
                id=new_id("toolresult"),
                binding_id=binding.id,
                task_id=binding.task_id,
                tool_name=binding.tool_name,
                mode=binding.mode,
                status=ToolBindingStatus.WAITING_APPROVAL,
                output={"approval_required": True, "approval_item": approval_item},
            )
        elif binding.mode == ToolMode.REAL:
            checkpoint_record = {
                "checkpoint_id": binding.checkpoint_id,
                "binding_id": binding.id,
                "tool_name": binding.tool_name,
                "capability": binding.capability,
                "task_title": binding.task_title,
            }
            self.checkpoint_store.append(checkpoint_record)
            result = ToolExecutionResult(
                id=new_id("toolresult"),
                binding_id=binding.id,
                task_id=binding.task_id,
                tool_name=binding.tool_name,
                mode=binding.mode,
                status=ToolBindingStatus.EXECUTED,
                output={
                    "executed": True,
                    "safe_local": True,
                    "capability": binding.capability,
                    "checkpoint_recorded": True,
                    "checkpoint_id": binding.checkpoint_id,
                },
            )
        else:
            result = ToolExecutionResult(
                id=new_id("toolresult"),
                binding_id=binding.id,
                task_id=binding.task_id,
                tool_name=binding.tool_name,
                mode=binding.mode,
                status=ToolBindingStatus.EXECUTED,
                output={
                    "dry_run": True,
                    "capability": binding.capability,
                    "planned_tool": binding.tool_name,
                    "reason": binding.reason,
                },
            )
        self.result_store.append(to_dict(result))
        return result
