"""
V107-V116 Self-Evolution Ops Layer.

This package continues after:
  V85 model decision engine
  V86 personal execution agent
  V87-V96 autonomy kernel
  V97-V106 operating governance layer

It adds production-grade self-evolution operations:
  V107 intent contract
  V108 context fusion
  V109 tool reliability
  V110 budget governor
  V111 privacy redaction
  V112 local/offline fallback
  V113 simulation lab
  V114 preference drift monitor
  V115 observability report
  V116 self-improvement loop
"""

from .schemas import (
    ContractStatus,
    BudgetStatus,
    PrivacyLevel,
    CircuitStatus,
    SimulationStatus,
    DriftStatus,
    ImprovementStatus,
    IntentContract,
    ContextPack,
    ReliabilityDecision,
    BudgetDecision,
    RedactionReport,
    FallbackPlan,
    SimulationResult,
    DriftReport,
    ObservabilityReport,
    ImprovementPlan,
    SelfEvolutionCycleResult,
)

from .intent_contract import IntentContractCompiler
from .context_fusion import ContextFusionEngine
from .tool_reliability import ToolReliabilityManager
from .budget_governor import BudgetGovernor
from .privacy_redactor import PrivacyRedactor
from .local_fallback import LocalFallbackPlanner
from .simulation_lab import SimulationLab
from .preference_drift import PreferenceDriftMonitor
from .observability_report import ObservabilityReporter
from .self_improvement_loop import SelfImprovementLoop, init_self_evolution_ops, run_self_evolution_cycle

__all__ = [
    "ContractStatus",
    "BudgetStatus",
    "PrivacyLevel",
    "CircuitStatus",
    "SimulationStatus",
    "DriftStatus",
    "ImprovementStatus",
    "IntentContract",
    "ContextPack",
    "ReliabilityDecision",
    "BudgetDecision",
    "RedactionReport",
    "FallbackPlan",
    "SimulationResult",
    "DriftReport",
    "ObservabilityReport",
    "ImprovementPlan",
    "SelfEvolutionCycleResult",
    "IntentContractCompiler",
    "ContextFusionEngine",
    "ToolReliabilityManager",
    "BudgetGovernor",
    "PrivacyRedactor",
    "LocalFallbackPlanner",
    "SimulationLab",
    "PreferenceDriftMonitor",
    "ObservabilityReporter",
    "SelfImprovementLoop",
    "init_self_evolution_ops",
    "run_self_evolution_cycle",
]
