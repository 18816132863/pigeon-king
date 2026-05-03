from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .schemas import ToolBindingReport, ToolMode, new_id, to_dict
from .tool_binder import ToolBinder
from .tool_executor import ToolExecutor
from .storage import JsonStore

class ToolBindingKernel:
    """Top-level real tool binding kernel."""

    def __init__(self, root: str | Path = ".real_tool_binding_state"):
        self.root = Path(root)
        self.binder = ToolBinder()
        self.executor = ToolExecutor(self.root)
        self.report_store = JsonStore(self.root / "tool_binding_reports.json")

    def run(self, ai_result) -> ToolBindingReport:
        bindings = self.binder.bind(ai_result)
        results = [self.executor.execute(binding) for binding in bindings]

        counts = {mode.value: 0 for mode in ToolMode}
        for b in bindings:
            counts[b.mode.value] += 1

        blocked = counts[ToolMode.BLOCKED.value]
        approval = counts[ToolMode.APPROVAL_REQUIRED.value]
        if blocked:
            final_status = "blocked"
        elif approval:
            final_status = "waiting_approval"
        else:
            final_status = "completed"

        report = ToolBindingReport(
            id=new_id("toolbinding_report"),
            run_id=ai_result.run_id,
            checkpoint_id=ai_result.checkpoint_id,
            bindings=bindings,
            results=results,
            mode_counts=counts,
            tool_count=len(bindings),
            real_count=counts[ToolMode.REAL.value],
            dry_run_count=counts[ToolMode.DRY_RUN.value],
            approval_count=approval,
            blocked_count=blocked,
            final_status=final_status,
        )
        self.report_store.append(to_dict(report))
        return report

_DEFAULT: Optional[ToolBindingKernel] = None

def init_tool_binding(root: str | Path = ".real_tool_binding_state") -> Dict:
    global _DEFAULT
    _DEFAULT = ToolBindingKernel(root)
    return {"status": "ok", "root": str(Path(root)), "default_entry": "core.real_tool_binding.ToolBindingKernel"}

def run_tool_binding(ai_result, root: str | Path = ".real_tool_binding_state") -> ToolBindingReport:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = ToolBindingKernel(root)
    return _DEFAULT.run(ai_result)
