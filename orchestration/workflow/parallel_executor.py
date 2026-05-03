"""
V86 Controlled Parallel Executor
并行计划器：只负责分组和稳定排序；真实执行仍由 WorkflowEngine 调用现有恢复链完成。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from orchestration.workflow.parallel_policy import ParallelClass, ParallelDecision, ParallelPolicy

try:
    from orchestration.workflow.workflow_registry import WorkflowStep
except Exception:  # pragma: no cover
    WorkflowStep = Any  # type: ignore


@dataclass
class ParallelGroupPlan:
    group_index: int
    safe_parallel: List[WorkflowStep] = field(default_factory=list)
    serial_required: List[WorkflowStep] = field(default_factory=list)
    approval_required: List[WorkflowStep] = field(default_factory=list)
    blocked: List[WorkflowStep] = field(default_factory=list)
    decisions: Dict[str, ParallelDecision] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_index": self.group_index,
            "safe_parallel": [s.step_id for s in self.safe_parallel],
            "serial_required": [s.step_id for s in self.serial_required],
            "approval_required": [s.step_id for s in self.approval_required],
            "blocked": [s.step_id for s in self.blocked],
            "decisions": {sid: d.to_dict() for sid, d in self.decisions.items()},
        }


class ParallelExecutor:
    def __init__(self, policy: Optional[ParallelPolicy] = None, max_parallel_steps: int = 4):
        self.policy = policy or ParallelPolicy()
        self.max_parallel_steps = max(1, int(max_parallel_steps or 1))

    def plan_group(self, steps: Iterable[WorkflowStep], group_index: int = 0, control_decision: Optional[Dict[str, Any]] = None) -> ParallelGroupPlan:
        plan = ParallelGroupPlan(group_index=group_index)
        for step in sorted(list(steps), key=lambda s: s.step_id):
            decision = self.policy.classify(step, control_decision=control_decision)
            plan.decisions[step.step_id] = decision
            if decision.parallel_class == ParallelClass.SAFE_PARALLEL:
                plan.safe_parallel.append(step)
            elif decision.parallel_class == ParallelClass.SERIAL_REQUIRED:
                plan.serial_required.append(step)
            elif decision.parallel_class == ParallelClass.APPROVAL_REQUIRED:
                plan.approval_required.append(step)
            else:
                plan.blocked.append(step)
        return plan
