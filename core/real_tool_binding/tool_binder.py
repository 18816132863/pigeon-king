from __future__ import annotations
from .schemas import ToolBinding, ToolBindingStatus, new_id
from .tool_registry import ToolRegistry
from .execution_policy import ToolExecutionPolicy

class ToolBinder:
    """Binds every TaskGraph node to a tool/capability and execution mode."""

    def __init__(self):
        self.registry = ToolRegistry()
        self.policy = ToolExecutionPolicy()

    def bind(self, ai_result) -> list[ToolBinding]:
        bindings = []
        for task in ai_result.task_graph.nodes:
            spec = self.registry.lookup(task.kind, task.title, ai_result.raw_input)
            mode, reason = self.policy.choose_mode(ai_result, task, spec)
            if mode.value == "blocked":
                status = ToolBindingStatus.BLOCKED
            elif mode.value == "approval_required":
                status = ToolBindingStatus.WAITING_APPROVAL
            else:
                status = ToolBindingStatus.BOUND

            bindings.append(ToolBinding(
                id=new_id("binding"),
                task_id=task.id,
                task_title=task.title,
                task_kind=task.kind,
                tool_name=spec["tool_name"],
                capability=spec["capability"],
                mode=mode,
                status=status,
                risk_level=task.risk_level.value,
                reason=reason,
                checkpoint_id=ai_result.checkpoint_id,
                metadata={"safe_real": bool(spec.get("safe_real")), "raw_goal": ai_result.raw_input},
            ))
        return bindings
