"""
V24.0 Real Tool Binding.

Binds AIShapeCore task graph nodes to concrete tool/capability slots with
safe execution modes:

real / dry_run / approval_required / blocked.

This layer does not blindly execute dangerous side effects. External send,
install, delete, payment, device-control, and credential-related tasks are
blocked or routed to approval by policy.
"""

from .schemas import (
    ToolMode,
    ToolBindingStatus,
    ToolBinding,
    ToolExecutionResult,
    ToolBindingReport,
)
from .tool_registry import ToolRegistry
from .execution_policy import ToolExecutionPolicy
from .tool_binder import ToolBinder
from .tool_executor import ToolExecutor
from .tool_binding_kernel import ToolBindingKernel, init_tool_binding, run_tool_binding

__all__ = [
    "ToolMode",
    "ToolBindingStatus",
    "ToolBinding",
    "ToolExecutionResult",
    "ToolBindingReport",
    "ToolRegistry",
    "ToolExecutionPolicy",
    "ToolBinder",
    "ToolExecutor",
    "ToolBindingKernel",
    "init_tool_binding",
    "run_tool_binding",
]
