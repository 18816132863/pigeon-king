"""
AI_SHAPE_CORE: Final AI-shape convergence layer.

This layer does not add another isolated module. It is the unified main chain
that closes V85-V316 into the target AI form:

one message -> goal contract -> memory/context -> constitution judge ->
world interface -> capability gap check -> task DAG -> dry-run/approval/
checkpoint/recovery -> memory writeback.

The default executor is safe: it does not create real external side effects.
"""

from .schemas import (
    RiskLevel,
    JudgeDecision,
    TaskStatus,
    MemoryKind,
    GoalContract,
    GoalNode,
    TaskNode,
    TaskGraph,
    WorldCapability,
    CapabilityGap,
    ExecutionTrace,
    MemoryRecord,
    AIShapeResult,
)
from .goal_strategy_kernel import GoalStrategyKernel
from .memory_kernel import UnifiedMemoryKernel
from .constitution_judge import ConstitutionJudge
from .world_interface import WorldInterface
from .capability_expansion import CapabilityExpansionKernel
from .task_graph_engine import TaskGraphEngine
from .ai_shape_core import AIShapeCore, YuanLingSystem, init_ai_shape_core, run_ai_shape_cycle

__all__ = [
    "RiskLevel",
    "JudgeDecision",
    "TaskStatus",
    "MemoryKind",
    "GoalContract",
    "GoalNode",
    "TaskNode",
    "TaskGraph",
    "WorldCapability",
    "CapabilityGap",
    "ExecutionTrace",
    "MemoryRecord",
    "AIShapeResult",
    "GoalStrategyKernel",
    "UnifiedMemoryKernel",
    "ConstitutionJudge",
    "WorldInterface",
    "CapabilityExpansionKernel",
    "TaskGraphEngine",
    "AIShapeCore",
    "YuanLingSystem",
    "init_ai_shape_core",
    "run_ai_shape_cycle",
    "AIShapeFinalizer",
    "run_main",
    "certify_final_shape",
]


# Final shape certification layer
from .finalizer import AIShapeFinalizer
from .main import run_main, certify_final_shape
