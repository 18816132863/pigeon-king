from __future__ import annotations

from governance.embodied_pending_state import CommitBarrier

from .dry_run_mirror import DryRunMirror
from .execution_trace_recorder import ExecutionTraceRecorder


class RealExecutionBroker:
    """Broker for real execution.

    In the embodied-pending-access state this broker is intentionally incapable
    of producing real-world side effects. Even if a caller passes a confirmation,
    payment/signature/physical/destructive/external commit actions stop at the
    commit barrier and are converted into mock/preview/approval artifacts.
    """

    def __init__(self) -> None:
        self.dry_run = DryRunMirror()
        self.traces = ExecutionTraceRecorder()
        self.commit_barrier = CommitBarrier()

    def prepare(self, action: dict, authorization: dict | None = None) -> dict:
        barrier = self.commit_barrier.check(action, authorization=authorization)
        if not barrier.allowed:
            dry = self.dry_run.mirror({**(action or {}), "blocked_by": "commit_barrier"})
            outcome = {
                "status": "commit_barrier_blocked",
                "barrier": barrier.to_dict(),
                "dry_run": dry,
                "real_side_effect": False,
            }
            trace = self.traces.record(action, outcome)
            return {**outcome, "trace": trace}

        authorized = bool(authorization and authorization.get("confirmed") is True)
        # Non-commit actions may be prepared/executed in sandbox, but still do not turn into live side effects here.
        dry = self.dry_run.mirror(action)
        status = "sandbox_ready_authorized_non_commit" if authorized else "dry_run_only"
        outcome = {
            "status": status,
            "dry_run": dry,
            "barrier": barrier.to_dict(),
            "real_side_effect": False,
        }
        trace = self.traces.record(action, outcome)
        return {**outcome, "trace": trace}
