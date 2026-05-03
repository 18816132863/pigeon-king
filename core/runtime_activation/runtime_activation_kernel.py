from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .schemas import (
    RuntimeActivationResult,
    ActivationStatus,
    CommandStatus,
    JobStatus,
    ScheduleStatus,
    DiagnosticStatus,
    PackageStatus,
    CompatibilityStatus,
    new_id,
)
from .command_bus import CommandBus
from .api_facade import ApiFacade
from .job_queue import JobQueue
from .scheduler_bridge import SchedulerBridge
from .state_inspector import StateInspector
from .diagnostic_engine import DiagnosticEngine
from .policy_simulator import PolicySimulator
from .artifact_packager import ArtifactPackager
from .compatibility_shim import CompatibilityShim


class RuntimeActivationKernel:
    """V146: one-shot runtime activation orchestrator."""

    def __init__(self, root: str | Path = ".", state_root: str | Path = ".runtime_activation_state"):
        self.root = Path(root)
        self.state_root = Path(state_root)
        self.command_bus = CommandBus(self.state_root)
        self.api = ApiFacade(self.state_root)
        self.jobs = JobQueue(self.state_root)
        self.scheduler = SchedulerBridge(self.state_root)
        self.inspector = StateInspector(self.root)
        self.compat = CompatibilityShim(self.root)
        self.diagnostic = DiagnosticEngine()
        self.policy = PolicySimulator()
        self.packager = ArtifactPackager(self.root)

    def run_cycle(self, goal: str) -> RuntimeActivationResult:
        run_id = new_id("activation")
        command = self.command_bus.accept(goal)
        cmd_result = self.command_bus.route(command)
        api_resp = self.api.handle("/runtime/activate", body={"goal": goal, "command_id": command.id})
        job = self.jobs.enqueue(command)
        job_done = self.jobs.run_next() or job
        schedule = self.scheduler.create_once(f"run:{command.intent}", job_done, next_run_hint="now")
        inspection = self.inspector.inspect()
        compat = self.compat.check()
        diag = self.diagnostic.build(inspection, compat)
        policy = self.policy.simulate(goal)
        package = self.packager.build_record("pigeon_king_v137_v146_runtime_activation_upgrade")

        if not policy.passed:
            status = ActivationStatus.BLOCKED
            next_action = "修复策略模拟失败后再激活"
        elif job_done.status == JobStatus.WAITING_APPROVAL:
            status = ActivationStatus.WAITING_APPROVAL
            next_action = "等待审批后继续执行队列任务"
        elif compat.status == CompatibilityStatus.INCOMPATIBLE or diag.status == DiagnosticStatus.FAIL:
            status = ActivationStatus.BLOCKED
            next_action = "补齐缺失层或修复诊断失败"
        elif compat.status == CompatibilityStatus.PARTIAL or diag.status == DiagnosticStatus.WARN:
            status = ActivationStatus.DEGRADED_READY
            next_action = "可降级运行，建议补齐缺失层后进入正式运行"
        else:
            status = ActivationStatus.READY
            next_action = "运行激活层就绪，可作为统一入口接收命令"

        checks = [
            cmd_result.status == CommandStatus.ROUTED,
            api_resp.status_code == 200,
            job_done.status in {JobStatus.COMPLETED, JobStatus.WAITING_APPROVAL},
            schedule.status == ScheduleStatus.DUE,
            inspection.status in {DiagnosticStatus.PASS, DiagnosticStatus.WARN},
            diag.status in {DiagnosticStatus.PASS, DiagnosticStatus.WARN},
            policy.passed,
            package.status == PackageStatus.CREATED,
            compat.status in {CompatibilityStatus.COMPATIBLE, CompatibilityStatus.PARTIAL},
        ]
        score = round(sum(1 for x in checks if x) / len(checks), 4)

        return RuntimeActivationResult(
            run_id=run_id,
            goal=goal,
            activation_status=status,
            command_status=cmd_result.status,
            api_status_code=api_resp.status_code,
            job_status=job_done.status,
            schedule_status=schedule.status,
            inspection_status=inspection.status,
            diagnostic_status=diag.status,
            policy_passed=policy.passed,
            package_status=package.status,
            compatibility_status=compat.status,
            score=score,
            next_action=next_action,
            details={
                "routed_to": cmd_result.routed_to,
                "route_reason": cmd_result.reason,
                "job_summary": job_done.result_summary,
                "diagnostic_recommendations": diag.recommendations,
                "policy": {"expected": policy.expected, "actual": policy.actual, "notes": policy.notes},
                "package_files": len(package.files),
                "missing_layers": compat.missing_layers,
            },
        )


_DEFAULT: Optional[RuntimeActivationKernel] = None


def init_runtime_activation(root: str | Path = ".", state_root: str | Path = ".runtime_activation_state") -> Dict:
    global _DEFAULT
    _DEFAULT = RuntimeActivationKernel(root, state_root)
    return {"status": "ok", "root": str(Path(root)), "state_root": str(Path(state_root)), "modules": 10}


def run_runtime_activation_cycle(goal: str, root: str | Path = ".", state_root: str | Path = ".runtime_activation_state") -> RuntimeActivationResult:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root) or _DEFAULT.state_root != Path(state_root):
        _DEFAULT = RuntimeActivationKernel(root, state_root)
    return _DEFAULT.run_cycle(goal)
