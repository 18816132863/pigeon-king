"""
V25.7 Personal Operating Agent Loop V2

A thin L3 orchestration loop that coordinates the organs without stealing their jobs:
- compile goal (core)
- build task graph (orchestration)
- judge/contract-check before execution (governance)
- enforce device seriality (orchestration/execution)
- propose memory writeback (memory guard)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

from core.goal_contract_v2 import GoalCompilerV2
from orchestration.durable_task_graph_v2 import TaskGraphBuilderV2
from orchestration.end_side_hard_serial_gate import EndSideAction, EndSideHardSerialGate
from memory_context.memory_writeback_guard_v2 import MemoryWritebackGuardV2


@dataclass
class OperatingLoopResult:
    goal_id: str
    task_nodes: int
    end_side_serialized: int
    memory_writeback_allowed: bool
    status: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class PersonalOperatingLoopV2:
    def __init__(self) -> None:
        self.goal_compiler = GoalCompilerV2()
        self.graph_builder = TaskGraphBuilderV2()
        self.serial_gate = EndSideHardSerialGate()
        self.memory_guard = MemoryWritebackGuardV2()

    def plan(self, user_intent: str, actions: List[Dict[str, object]]) -> OperatingLoopResult:
        goal = self.goal_compiler.compile(user_intent)
        graph = self.graph_builder.from_goal(goal.goal_id, actions)

        end_actions: List[EndSideAction] = []
        for node in graph.end_side_nodes():
            end_actions.append(
                EndSideAction(
                    action_id=node.node_id,
                    kind="device_action",
                    name=node.action,
                    idempotency_key=f"{goal.goal_id}:{node.node_id}",
                    timeout_profile="device_default",
                    verification_policy="post_verify_or_pending_verify",
                    depends_on=node.depends_on,
                )
            )
        serial_plan = self.serial_gate.normalize(goal.goal_id, end_actions)

        memory_decision = self.memory_guard.evaluate({
            "memory_type": "episodic",
            "content": f"planned goal {goal.goal_id} with {len(graph.nodes)} nodes",
            "confidence": 0.8,
            "source_goal_id": goal.goal_id,
        })

        return OperatingLoopResult(
            goal_id=goal.goal_id,
            task_nodes=len(graph.nodes),
            end_side_serialized=len(serial_plan.serial_device_actions),
            memory_writeback_allowed=memory_decision.allowed,
            status="planned",
        )
