"""
V97-V106 Personal Operating Agent Governance Layer.

This package sits above:
  - V85 model decision engine
  - V86 personal execution agent
  - V87-V96 autonomy kernel

It adds OS-level governance, permissions, connector marketplace, MCP management,
plugin sandboxing, specialist handoff, multi-agent coordination, recovery ledger,
benchmark evaluation and release governance.
"""

from .schemas import (
    RuleSeverity,
    DecisionStatus,
    PermissionScope,
    TrustLevel,
    ReleaseStage,
    ConstitutionDecision,
    PermissionGrant,
    ConnectorCandidate,
    MCPServerSpec,
    PluginSandboxReport,
    SpecialistAgent,
    HandoffRecord,
    RecoveryEntry,
    BenchmarkCase,
    BenchmarkResult,
    ReleaseGateResult,
    OperatingCycleResult,
)

from .constitution_kernel import ConstitutionKernel
from .permission_vault import PermissionVault
from .connector_catalog import ConnectorCatalog
from .mcp_manager import MCPManager
from .plugin_sandbox import PluginSandboxManager
from .specialist_handoff import SpecialistHandoffManager
from .multi_agent_coordinator import MultiAgentCoordinator
from .recovery_ledger import RecoveryLedger
from .evaluation_benchmark import EvaluationBenchmark
from .release_governor import ReleaseGovernor
from .operating_orchestrator import OperatingAgentOrchestrator, init_operating_agent, run_operating_cycle

__all__ = [
    "RuleSeverity",
    "DecisionStatus",
    "PermissionScope",
    "TrustLevel",
    "ReleaseStage",
    "ConstitutionDecision",
    "PermissionGrant",
    "ConnectorCandidate",
    "MCPServerSpec",
    "PluginSandboxReport",
    "SpecialistAgent",
    "HandoffRecord",
    "RecoveryEntry",
    "BenchmarkCase",
    "BenchmarkResult",
    "ReleaseGateResult",
    "OperatingCycleResult",
    "ConstitutionKernel",
    "PermissionVault",
    "ConnectorCatalog",
    "MCPManager",
    "PluginSandboxManager",
    "SpecialistHandoffManager",
    "MultiAgentCoordinator",
    "RecoveryLedger",
    "EvaluationBenchmark",
    "ReleaseGovernor",
    "OperatingAgentOrchestrator",
    "init_operating_agent",
    "run_operating_cycle",
]
