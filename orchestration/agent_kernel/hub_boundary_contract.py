"""
V23.3 Agent Hub Boundary Contract.

agent_kernel is the total orchestrator, not an all-powerful bucket.
It may dispatch, sequence, and summarize, but it must not bypass:
- L5 Governance for risk decisions
- L4 Execution / outbox for real side effects
- L2 Memory Kernel for durable memory writes
- L6 Context Resume / Recovery for interruption recovery
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Iterable, List


class HubOperation(str, Enum):
    RECEIVE_GOAL = "receive_goal"
    COMPILE_GOAL = "compile_goal"
    BUILD_TASK_GRAPH = "build_task_graph"
    DISPATCH_TASK = "dispatch_task"
    SUMMARIZE_RESULT = "summarize_result"
    REQUEST_RISK_DECISION = "request_risk_decision"
    REQUEST_EXECUTION = "request_execution"
    REQUEST_MEMORY_WRITE = "request_memory_write"
    REQUEST_RECOVERY = "request_recovery"
    DIRECT_RISK_DECISION = "direct_risk_decision"
    DIRECT_TOOL_CALL = "direct_tool_call"
    DIRECT_LONG_TERM_MEMORY_WRITE = "direct_long_term_memory_write"
    DIRECT_INSTALL_OR_PROMOTE = "direct_install_or_promote"


@dataclass(frozen=True)
class HubBoundaryDecision:
    operation: str
    allowed: bool
    required_owner: str
    reason: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


_ALLOWED_DIRECT = {
    HubOperation.RECEIVE_GOAL: ("L3 Orchestration", "agent_kernel may receive and normalize a user goal"),
    HubOperation.COMPILE_GOAL: ("L3 Orchestration", "agent_kernel may invoke goal_compiler"),
    HubOperation.BUILD_TASK_GRAPH: ("L3 Orchestration", "agent_kernel may invoke task_graph"),
    HubOperation.DISPATCH_TASK: ("L3 Orchestration", "agent_kernel may dispatch tasks to their owners"),
    HubOperation.SUMMARIZE_RESULT: ("L3 Orchestration", "agent_kernel may assemble the final report"),
    HubOperation.REQUEST_RISK_DECISION: ("L5 Governance", "risk decision must be delegated to unified_judge"),
    HubOperation.REQUEST_EXECUTION: ("L4 Execution", "real side effects must go through execution/outbox"),
    HubOperation.REQUEST_MEMORY_WRITE: ("L2 Memory Context", "durable memory writes must go through memory_kernel"),
    HubOperation.REQUEST_RECOVERY: ("L6 Infrastructure", "resume/recovery must use context_resume/recovery state"),
}

_DENIED_DIRECT = {
    HubOperation.DIRECT_RISK_DECISION: ("L5 Governance", "agent_kernel cannot hardcode final allow/confirm/deny"),
    HubOperation.DIRECT_TOOL_CALL: ("L4 Execution", "agent_kernel cannot directly call device tools or external tools"),
    HubOperation.DIRECT_LONG_TERM_MEMORY_WRITE: ("L2 Memory Context", "agent_kernel cannot directly persist long-term memory"),
    HubOperation.DIRECT_INSTALL_OR_PROMOTE: ("L5 Governance + extension gate", "capability install/promotion needs sandbox evaluation and governance"),
}


def evaluate_hub_operation(operation: str) -> HubBoundaryDecision:
    op = HubOperation(operation)
    if op in _ALLOWED_DIRECT:
        owner, reason = _ALLOWED_DIRECT[op]
        return HubBoundaryDecision(op.value, True, owner, reason)
    owner, reason = _DENIED_DIRECT[op]
    return HubBoundaryDecision(op.value, False, owner, reason)


def evaluate_hub_sequence(operations: Iterable[str]) -> List[Dict[str, object]]:
    return [evaluate_hub_operation(op).to_dict() for op in operations]


def assert_no_boundary_conflict(operations: Iterable[str]) -> Dict[str, object]:
    decisions = evaluate_hub_sequence(operations)
    denied = [d for d in decisions if not d["allowed"]]
    return {
        "passed": not denied,
        "denied_count": len(denied),
        "decisions": decisions,
    }
