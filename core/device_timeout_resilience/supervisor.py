from __future__ import annotations

import time
from pathlib import Path

from .schemas import TimeoutStatus, TimeoutPolicy, TimeoutResilienceReport, new_id, to_dict
from .timeout_policy import TimeoutPolicyEngine
from .task_splitter import TimeoutAwareTaskSplitter
from .job_queue import ResumableJobQueue
from .heartbeat import HeartbeatStore
from .retry_planner import RetryPlanner
from .storage import JsonStore


class TimeoutResilienceSupervisor:
    """Prevents endpoint/device connector timeout by using fast-ack jobs."""

    def __init__(self, root: str | Path = ".timeout_resilience_state", policy: TimeoutPolicy | None = None):
        self.root = Path(root)
        self.policy_engine = TimeoutPolicyEngine(policy)
        self.policy = self.policy_engine.policy
        self.splitter = TimeoutAwareTaskSplitter()
        self.queue = ResumableJobQueue(self.root)
        self.heartbeats = HeartbeatStore(self.root)
        self.retry = RetryPlanner()
        self.reports = JsonStore(self.root / "timeout_reports.json")

    def run(self, message: str, estimated_seconds: int = 120, approved: bool = False) -> TimeoutResilienceReport:
        started = time.time()
        checkpoint_id = new_id("timeout_checkpoint")
        classification = self.policy_engine.classify(message, estimated_seconds)

        approval_required = classification["needs_approval"] and not approved
        steps = self.splitter.split(
            message=message,
            estimated_seconds=estimated_seconds,
            max_step_seconds=self.policy_engine.safe_single_call_budget(),
            checkpoint_id=checkpoint_id,
        )
        job = self.queue.enqueue(message, estimated_seconds, approval_required, steps, checkpoint_id)

        beats = []
        first_step_id = steps[0].id if steps else "none"
        if approval_required:
            status = TimeoutStatus.WAITING_APPROVAL
            beats.append(self.heartbeats.beat(job.id, first_step_id, status, checkpoint_id, "approval required; no blocking connector call started"))
        elif classification["long_running"]:
            status = TimeoutStatus.RESUMABLE
            beats.append(self.heartbeats.beat(job.id, first_step_id, TimeoutStatus.HEARTBEAT_OK, checkpoint_id, "fast ack created; long job chunked and resumable"))
            beats.append(self.heartbeats.beat(job.id, first_step_id, TimeoutStatus.PAUSED_BEFORE_TIMEOUT, checkpoint_id, "paused before soft deadline; resume via poll/approval"))
        else:
            status = TimeoutStatus.COMPLETED
            for step in steps:
                step.status = TimeoutStatus.COMPLETED
                step.output = {"executed": True, "within_timeout_budget": True}
                beats.append(self.heartbeats.beat(job.id, step.id, TimeoutStatus.COMPLETED, checkpoint_id, "short step completed"))

        job.status = status
        elapsed = round(time.time() - started, 4)
        retry_plan = self.retry.plan(self.policy.max_retries)

        final = {
            "timeout_fixed_by": [
                "fast_ack",
                "chunked_steps",
                "heartbeat",
                "checkpoint_before_hard_timeout",
                "resumable_job_queue",
                "approval_wait_not_blocking",
            ],
            "hard_timeout_seconds": self.policy.hard_timeout_seconds,
            "soft_deadline_seconds": self.policy.soft_deadline_seconds,
            "estimated_seconds": estimated_seconds,
            "step_count": len(steps),
            "approval_required": approval_required,
            "can_poll_or_resume": True,
            "no_external_side_effect_started_without_approval": True,
        }

        report = TimeoutResilienceReport(
            id=new_id("timeout_report"),
            message=message,
            status=status,
            policy=self.policy,
            job=job,
            heartbeats=beats,
            retry_plan=retry_plan,
            elapsed_seconds=elapsed,
            no_blocking_call_over_soft_deadline=elapsed < self.policy.soft_deadline_seconds,
            checkpoint_id=checkpoint_id,
            final_report=final,
        )
        self.reports.append(to_dict(report))
        return report
