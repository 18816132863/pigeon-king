"""
V87-V96 Autonomy Upgrade Kernel.

This package upgrades the V86 personal execution agent into a bounded
self-evolving personal operating agent.

Public entrypoints:
  - AutonomyOrchestrator
  - run_autonomy_cycle
  - init_autonomy_system
"""

from .schemas import (
    RiskLevel,
    MemoryKind,
    ConnectorKind,
    CapabilityGapStatus,
    ExtensionStatus,
    ApprovalStatus,
    TaskRunStatus,
    AutonomyCycleResult,
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
from .autonomy_orchestrator import AutonomyOrchestrator, run_autonomy_cycle, init_autonomy_system

__all__ = [
    "RiskLevel",
    "MemoryKind",
    "ConnectorKind",
    "CapabilityGapStatus",
    "ExtensionStatus",
    "ApprovalStatus",
    "TaskRunStatus",
    "AutonomyCycleResult",
    "MemoryKernel",
    "WorldInterface",
    "CapabilityGapAnalyzer",
    "ExtensionSandbox",
    "ApprovalInterruptManager",
    "TraceAudit",
    "QualityEvaluator",
    "StrategyEvolver",
    "ContinuousTaskRunner",
    "AutonomyOrchestrator",
    "run_autonomy_cycle",
    "init_autonomy_system",
]
from .goal_strategy_kernel import GoalStrategyKernel
from .task_graph_compiler import TaskGraphCompiler
