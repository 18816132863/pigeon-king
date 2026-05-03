from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional

from .schemas import (
    AIShapeResult,
    JudgeDecision,
    MemoryKind,
    TaskStatus,
    new_id,
)
from .goal_strategy_kernel import GoalStrategyKernel
from .memory_kernel import UnifiedMemoryKernel
from .constitution_judge import ConstitutionJudge
from .world_interface import WorldInterface
from .capability_expansion import CapabilityExpansionKernel
from .task_graph_engine import TaskGraphEngine

class AIShapeCore:
    """Final unified AI-shape main chain.

    This is the single entrance that closes V85-V316 into the target form.
    """

    def __init__(self, root: str | Path = ".ai_shape_core_state"):
        self.root = Path(root)
        self.goal_strategy = GoalStrategyKernel()
        self.memory = UnifiedMemoryKernel(self.root)
        self.judge = ConstitutionJudge()
        self.world = WorldInterface()
        self.capabilities = CapabilityExpansionKernel()
        self.tasks = TaskGraphEngine()

    def run(self, raw_input: str) -> AIShapeResult:
        run_id = new_id("aishape")
        memories = self.memory.search(raw_input)
        contract = self.goal_strategy.compile(raw_input)
        world_caps = self.world.capabilities()
        contract.information_sources = list(dict.fromkeys(contract.information_sources + self.world.source_list(raw_input)))

        decision, judge_reasons = self.judge.judge(contract)
        gaps = self.capabilities.analyze(contract, world_caps)
        graph = self.tasks.compile(contract, decision)
        traces = self.tasks.execute_safe(graph, decision)

        auto_executed = [n.title for n in graph.nodes if n.status == TaskStatus.COMPLETED]
        approval_tasks = [n.title for n in graph.nodes if n.status == TaskStatus.WAITING_APPROVAL]
        blocked_tasks = [n.title for n in graph.nodes if n.status == TaskStatus.BLOCKED]

        recovery = [
            f"使用 checkpoint 恢复：{graph.checkpoint_id}",
            "如果验证失败，回滚到覆盖前工作区快照",
            "如果工具失败，进入降级模式：仅输出计划/报告，不执行副作用",
            "如果审批被拒绝，保留自动完成部分并终止真实副作用",
        ]

        memory_writes = [
            self.memory.write(MemoryKind.EPISODIC, f"run.{run_id}.input", raw_input, 0.9, "ai_shape_core"),
            self.memory.write(MemoryKind.PROCEDURAL, "latest.execution_shape", "goal->judge->world->capability->DAG->checkpoint->memory", 0.92, "ai_shape_core"),
        ]
        if "压缩包" in raw_input or "命令" in raw_input:
            memory_writes.append(self.memory.write(MemoryKind.LONG_TERM, "delivery.preference.confirmed", "继续优先交付完整覆盖包 + 一条命令", 0.95, "ai_shape_core"))

        if decision == JudgeDecision.BLOCK:
            final_status = "blocked_by_constitution"
        elif approval_tasks:
            final_status = "waiting_approval_with_safe_parts_completed"
        else:
            final_status = "completed_as_safe_ai_shape_cycle"

        completion = {
            "has_goal_tree": bool(contract.goal_tree),
            "has_task_graph_dag": bool(graph.nodes and graph.edges),
            "has_information_sources": bool(contract.information_sources),
            "has_risk_classification": bool(contract.risk_level.value),
            "has_auto_execution_part": bool(auto_executed),
            "has_approval_part": bool(approval_tasks) or contract.risk_level.value.startswith("L0") is False,
            "has_checkpoint": bool(graph.checkpoint_id),
            "has_execution_result": bool(traces),
            "has_recovery_plan": bool(recovery),
            "has_memory_writeback": bool(memory_writes),
            "judge_reasons": judge_reasons,
            "matched_memory_count": len(memories),
        }

        return AIShapeResult(
            run_id=run_id,
            raw_input=raw_input,
            final_status=final_status,
            judge_decision=decision,
            risk_level=contract.risk_level,
            goal_contract=contract,
            task_graph=graph,
            information_sources=contract.information_sources,
            auto_executed_tasks=auto_executed,
            approval_tasks=approval_tasks,
            blocked_tasks=blocked_tasks,
            checkpoint_id=graph.checkpoint_id,
            execution_traces=traces,
            capability_gaps=gaps,
            recovery_plan=recovery,
            memory_writes=memory_writes,
            world_capabilities=world_caps,
            completion_report=completion,
        )

# User-facing alias requested by earlier architecture direction.
YuanLingSystem = AIShapeCore

_DEFAULT: Optional[AIShapeCore] = None

def init_ai_shape_core(root: str | Path = ".ai_shape_core_state") -> Dict:
    global _DEFAULT
    _DEFAULT = AIShapeCore(root)
    return {"status": "ok", "root": str(Path(root)), "main_entry": "core.ai_shape_core.AIShapeCore", "shape": "final"}

def run_ai_shape_cycle(raw_input: str, root: str | Path = ".ai_shape_core_state") -> AIShapeResult:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = AIShapeCore(root)
    return _DEFAULT.run(raw_input)
