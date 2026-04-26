from __future__ import annotations

from .dry_run_mirror import DryRunMirror
from .execution_trace_recorder import ExecutionTraceRecorder


class RealExecutionBroker:
    """Broker for real execution. It defaults to dry-run unless authorization is explicitly recorded."""

    def __init__(self) -> None:
        self.dry_run = DryRunMirror()
        self.traces = ExecutionTraceRecorder()

    def prepare(self, action: dict, authorization: dict | None = None) -> dict:
        authorized = bool(authorization and authorization.get("confirmed") is True)
        if not authorized:
            dry = self.dry_run.mirror(action)
            trace = self.traces.record(action, dry)
            return {"status": "dry_run_only", "dry_run": dry, "trace": trace, "real_side_effect": False}
        outcome = {"status": "ready_for_real_executor", "real_side_effect": True}
        trace = self.traces.record(action, outcome)
        return {"status": "ready_for_real_execution", "outcome": outcome, "trace": trace, "real_side_effect": True}
