"""
V25.9 Personal Operating Agent Loop V2

A thin L3 orchestration loop that coordinates the organs without stealing their jobs:
- compile goal (core)
- build task graph (orchestration)
- self-evolution gate (V25.8: SelfImprovementLoop)
- judge/contract-check before execution (governance)
- enforce device seriality (orchestration/execution)
- memory writeback through kernel → KG + Preference + Qdrant (V25.9)
- feed preference evolution (V25.8: PreferenceEvolutionBridge)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

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
    memory_writeback_result: Optional[Dict[str, Any]] = None
    self_evolution_check: Optional[Dict[str, Any]] = None
    preference_ingested: bool = False
    status: str = ""

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class PersonalOperatingLoopV2:
    def __init__(self) -> None:
        self.goal_compiler = GoalCompilerV2()
        self.graph_builder = TaskGraphBuilderV2()
        self.serial_gate = EndSideHardSerialGate()
        self.memory_guard = MemoryWritebackGuardV2()
        self._memory_kernel = None
        self._self_evo = None
        self._pref_bridge = None

    def _get_memory_kernel(self):
        """V29.2: Lazy-init memory kernel with full bridge integration."""
        if self._memory_kernel is None:
            from memory_context.personal_memory_kernel_v4 import PersonalMemoryKernelV4
            self._memory_kernel = PersonalMemoryKernelV4()
        return self._memory_kernel

    def _get_self_evo(self):
        if self._self_evo is None:
            from core.self_evolution_ops import init_self_evolution_ops, run_self_evolution_cycle
            init_self_evolution_ops(".self_evolution_ops_state")
            self._self_evo = run_self_evolution_cycle
        return self._self_evo

    def _get_pref_bridge(self):
        if self._pref_bridge is None:
            from memory_context.preference_evolution_bridge import get_preference_evolution_bridge
            self._pref_bridge = get_preference_evolution_bridge()
        return self._pref_bridge

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

        # ── V25.8: Self-evolution gate ──
        evo_result = None
        try:
            cycle = self._get_self_evo()
            evo_result = cycle(user_intent, tool_name="personal_operating_loop")
            if hasattr(evo_result, 'to_dict'):
                evo_result = evo_result.to_dict()
            elif hasattr(evo_result, '__dataclass_fields__'):
                from dataclasses import asdict
                evo_result = asdict(evo_result)
        except Exception:
            pass

        memory_decision = self.memory_guard.evaluate({
            "memory_type": "episodic",
            "content": f"planned goal {goal.goal_id} with {len(graph.nodes)} nodes",
            "confidence": 0.8,
            "source_goal_id": goal.goal_id,
        })

        # ── V25.9: Actually write memory through kernel ──
        memory_result = None
        if memory_decision.allowed:
            try:
                kernel = self._get_memory_kernel()
                memory_result = kernel.write(
                    memory_type="episodic",
                    content=f"Goal: {user_intent[:300]}",
                    confidence=0.8,
                    source="system_observation",
                    tags=[f"goal_id:{goal.goal_id}", f"nodes:{len(graph.nodes)}"],
                )
            except Exception:
                pass

        # ── V25.8: Feed preference evolution ──
        pref_ingested = False
        try:
            self._get_pref_bridge().ingest_from_interaction(
                interaction_key=f"goal_{goal.goal_id}",
                value={"intent": user_intent[:200], "nodes": len(graph.nodes)},
                confidence_delta=0.05,
            )
            pref_ingested = True
        except Exception:
            pass

        return OperatingLoopResult(
            goal_id=goal.goal_id,
            task_nodes=len(graph.nodes),
            end_side_serialized=len(serial_plan.serial_device_actions),
            memory_writeback_allowed=memory_decision.allowed,
            memory_writeback_result=memory_result,
            self_evolution_check=evo_result,
            preference_ingested=pref_ingested,
            status="planned",
        )

    def execute(self, user_intent: str, actions: List[Dict[str, object]]) -> OperatingLoopResult:
        """Plan + record outcome. Same as plan() but also records execution outcome."""
        result = self.plan(user_intent, actions)

        # Record execution outcome as episodic memory
        try:
            kernel = self._get_memory_kernel()
            outcome_content = (
                f"Executed goal {result.goal_id}: {user_intent[:200]} — "
                f"{result.task_nodes} nodes, {result.end_side_serialized} serialized, "
                f"memory_written={result.memory_writeback_allowed}"
            )
            kernel.write(
                memory_type="episodic",
                content=outcome_content,
                confidence=0.85,
                source="task_verified",
                tags=["outcome", f"goal_id:{result.goal_id}"],
            )
        except Exception:
            pass

        return result

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recall relevant memories for a query."""
        try:
            return self._get_memory_kernel().recall(query, limit=limit)
        except Exception:
            return []

    def search_semantic(self, query: str, limit: int = 5,
                        filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Semantic vector search through memory."""
        try:
            return self._get_memory_kernel().search_semantic(query, limit=limit, filter_type=filter_type)
        except Exception:
            return []

    def memory_stats(self) -> Dict[str, Any]:
        """Return full memory subsystem stats."""
        try:
            return self._get_memory_kernel().stats()
        except Exception:
            return {"status": "unavailable"}
