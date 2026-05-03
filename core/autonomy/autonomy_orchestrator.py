from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, List

from .schemas import (
    AutonomyCycleResult,
    RiskLevel,
    TaskRunStatus,
    CapabilityGapStatus,
    ExtensionStatus,
    ApprovalStatus,
    new_id,
)
from .memory_kernel import MemoryKernel
from .world_interface import WorldInterface
from .capability_gap import CapabilityGapAnalyzer
from .extension_sandbox import ExtensionSandbox
from .approval_interrupt import ApprovalInterruptManager
from .trace_audit import TraceAudit
from .quality_evaluator import QualityEvaluator
from .strategy_evolver import StrategyEvolver
from .continuous_task_runner import ContinuousTaskRunner


class AutonomyOrchestrator:
    """V96: top-level autonomy orchestrator.

    It coordinates V87-V95 modules:
      memory -> world interface -> capability gap -> sandbox proposal ->
      approval interrupt -> trace -> quality -> strategy evolution.
    """

    def __init__(self, root: str | Path = ".autonomy_state"):
        self.root = Path(root)
        self.memory = MemoryKernel(self.root)
        self.world = WorldInterface(self.root)
        self.gap = CapabilityGapAnalyzer()
        self.sandbox = ExtensionSandbox(self.root)
        self.approvals = ApprovalInterruptManager(self.root)
        self.trace = TraceAudit(self.root)
        self.quality = QualityEvaluator(self.root)
        self.strategy = StrategyEvolver(self.root)
        self.continuous = ContinuousTaskRunner(self.root)

    def _estimate_risk(self, goal: str, required: List[str]) -> RiskLevel:
        if any(x in goal for x in ["转账", "支付", "删除", "发送邮件", "发给客户", "安装未知", "隐私导出"]):
            return RiskLevel.L4
        if any(x in required for x in ["external_action", "connector_management"]):
            return RiskLevel.L3
        if any(x in goal for x in ["修改", "覆盖", "执行命令", "写入"]):
            return RiskLevel.L2
        return RiskLevel.L1

    def run_cycle(self, goal: str, context: Optional[Dict] = None) -> AutonomyCycleResult:
        context = context or {}
        run_id = new_id("autonomy")
        self.trace.record(run_id, "goal_received", "Goal received", {"goal": goal})

        memory_summary = self.memory.summarize_for_prompt()
        self.trace.record(run_id, "memory_loaded", "Memory summary loaded", memory_summary)

        connectors = self.world.list_connectors()
        connector_caps = sorted({cap for c in connectors for cap in c.capabilities})
        gap = self.gap.analyze(goal, connector_capabilities=connector_caps)
        self.trace.record(run_id, "capability_gap_analyzed", gap.explanation, {
            "required": gap.required_capabilities,
            "missing": gap.missing_capabilities,
            "status": gap.status.value,
        })

        matches = self.world.match_capabilities(gap.required_capabilities)
        risk = self._estimate_risk(goal, gap.required_capabilities)
        approval = self.approvals.create_ticket(
            goal=goal,
            action_summary=f"Execute autonomy cycle with capabilities: {', '.join(gap.required_capabilities)}",
            risk_level=risk,
            reason="Risk policy requires approval for external side effects." if risk in {RiskLevel.L3, RiskLevel.L4} else "",
        )
        self.trace.record(run_id, "risk_judged", f"Risk={risk.value}, approval={approval.status.value}", {"risk": risk.value})

        extension_status = None
        if gap.status == CapabilityGapStatus.NEED_EXTENSION:
            proposal = self.sandbox.propose(
                capability_name=gap.missing_capabilities[0] if gap.missing_capabilities else "unknown_capability",
                source_type="trusted_catalog",
                risk_level=RiskLevel.L3,
            )
            evaluated = self.sandbox.evaluate(proposal.id)
            extension_status = evaluated.status
            self.trace.record(run_id, "extension_evaluated", "Extension sandbox evaluated", {
                "proposal_id": evaluated.id,
                "status": evaluated.status.value,
                "score": evaluated.evaluation_score,
            })

        blocked = approval.status == ApprovalStatus.PENDING
        result_payload = {
            "has_plan": True,
            "has_next_action": True,
            "actionable": not blocked,
            "steps": 7,
            "gap_status": gap.status.value,
            "approval": approval.status.value,
            "connector_matches": len(matches),
        }
        q = self.quality.evaluate(run_id, goal, result_payload, risk_blocked=blocked)
        self.trace.record(run_id, "quality_evaluated", "Quality evaluated", {"score": q.final_score, "passed": q.passed, "issues": q.issues})

        changed_rules = self.strategy.evolve_from_quality(q)
        self.trace.record(run_id, "strategy_evolved", "Strategy evolved", {"changed_rules": [r.name for r in changed_rules]})

        mem_updates = 0
        self.memory.record_episode(goal, outcome="waiting_for_approval" if blocked else "cycle_completed", lessons=q.issues)
        mem_updates += 1
        if q.passed:
            self.memory.record_procedure(
                name="autonomy_cycle_success",
                steps=[
                    "load_memory",
                    "match_connectors",
                    "analyze_capability_gap",
                    "judge_risk",
                    "approval_gate",
                    "evaluate_quality",
                    "write_experience",
                ],
                success_score=q.final_score,
            )
            mem_updates += 1

        status = TaskRunStatus.WAITING_APPROVAL if blocked else (TaskRunStatus.COMPLETED if q.passed else TaskRunStatus.PARTIAL)
        next_action = "等待人工审批后恢复执行" if blocked else "可进入执行图实际工具调用阶段"

        events = self.trace.list_run(run_id)
        return AutonomyCycleResult(
            run_id=run_id,
            goal=goal,
            status=status,
            memory_updates=mem_updates,
            connector_matches=len(matches),
            capability_gap_status=gap.status,
            approval_status=approval.status,
            extension_status=extension_status,
            quality_score=q.final_score,
            trace_events=len(events),
            next_action=next_action,
            details={
                "required_capabilities": gap.required_capabilities,
                "missing_capabilities": gap.missing_capabilities,
                "risk_level": risk.value,
                "approval_ticket": approval.id,
                "quality_issues": q.issues,
            },
        )


_DEFAULT: Optional[AutonomyOrchestrator] = None


def init_autonomy_system(root: str | Path = ".autonomy_state") -> Dict:
    global _DEFAULT
    _DEFAULT = AutonomyOrchestrator(root)
    return {
        "status": "ok",
        "root": str(Path(root)),
        "connectors": len(_DEFAULT.world.list_connectors()),
        "strategy_rules": len(_DEFAULT.strategy.list_rules()),
    }


def run_autonomy_cycle(goal: str, context: Optional[Dict] = None, root: str | Path = ".autonomy_state") -> AutonomyCycleResult:
    global _DEFAULT
    if _DEFAULT is None or Path(root) != _DEFAULT.root:
        _DEFAULT = AutonomyOrchestrator(root)
    return _DEFAULT.run_cycle(goal, context=context)
