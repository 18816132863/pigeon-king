"""
V167-V196 Operations Intelligence Upgrade.

This package adds a 30-version operational intelligence layer above:
  V85-V166 model routing, execution agent, autonomy, governance, ops,
  operating spine, release hardening, runtime activation, action bridge,
  and personalization.

V167-V196 turns the system into an operationally measurable loop:
roadmap -> portfolio -> experiments -> metrics -> data -> risk/incidents ->
cost/performance/token -> eval/learning -> compliance/security ->
stakeholder outputs -> audit/dashboard -> master operations kernel.
"""

from .schemas import (
    IntelligenceStatus,
    PriorityLevel,
    RiskLevel,
    ReportLevel,
    VersionFeature,
    IntelligenceArtifact,
    OperationsIntelligenceResult,
)

from .v167_roadmap_planner import RoadmapPlanner
from .v168_portfolio_manager import PortfolioManager
from .v169_experiment_designer import ExperimentDesigner
from .v170_metrics_kpi_engine import MetricsKPIEngine
from .v171_data_ingestion_hub import DataIngestionHub
from .v172_data_quality_gate import DataQualityGate
from .v173_report_generator import ReportGenerator
from .v174_decision_memo_builder import DecisionMemoBuilder
from .v175_risk_register import RiskRegister
from .v176_incident_manager import IncidentManager
from .v177_slo_manager import SLOManager
from .v178_cost_analyzer import CostAnalyzer
from .v179_performance_profiler import PerformanceProfiler
from .v180_token_optimizer import TokenOptimizer
from .v181_prompt_policy_compiler import PromptPolicyCompiler
from .v182_eval_dataset_builder import EvalDatasetBuilder
from .v183_ab_test_runner import ABTestRunner
from .v184_continuous_learning_queue import ContinuousLearningQueue
from .v185_knowledge_freshness_monitor import KnowledgeFreshnessMonitor
from .v186_compliance_checklist import ComplianceChecklistEngine
from .v187_data_retention_manager import DataRetentionManager
from .v188_secret_rotation_advisor import SecretRotationAdvisor
from .v189_connector_permission_review import ConnectorPermissionReviewer
from .v190_multichannel_output_router import MultiChannelOutputRouter
from .v191_stakeholder_briefing import StakeholderBriefingGenerator
from .v192_release_notes_generator import ReleaseNotesGenerator
from .v193_audit_exporter import AuditExporter
from .v194_health_dashboard import HealthDashboard
from .v195_executive_summary_packager import ExecutiveSummaryPackager
from .v196_operations_intelligence_kernel import (
    OperationsIntelligenceKernel,
    init_operations_intelligence,
    run_operations_intelligence_cycle,
)

__all__ = [
    "IntelligenceStatus",
    "PriorityLevel",
    "RiskLevel",
    "ReportLevel",
    "VersionFeature",
    "IntelligenceArtifact",
    "OperationsIntelligenceResult",
    "RoadmapPlanner",
    "PortfolioManager",
    "ExperimentDesigner",
    "MetricsKPIEngine",
    "DataIngestionHub",
    "DataQualityGate",
    "ReportGenerator",
    "DecisionMemoBuilder",
    "RiskRegister",
    "IncidentManager",
    "SLOManager",
    "CostAnalyzer",
    "PerformanceProfiler",
    "TokenOptimizer",
    "PromptPolicyCompiler",
    "EvalDatasetBuilder",
    "ABTestRunner",
    "ContinuousLearningQueue",
    "KnowledgeFreshnessMonitor",
    "ComplianceChecklistEngine",
    "DataRetentionManager",
    "SecretRotationAdvisor",
    "ConnectorPermissionReviewer",
    "MultiChannelOutputRouter",
    "StakeholderBriefingGenerator",
    "ReleaseNotesGenerator",
    "AuditExporter",
    "HealthDashboard",
    "ExecutiveSummaryPackager",
    "OperationsIntelligenceKernel",
    "init_operations_intelligence",
    "run_operations_intelligence_cycle",
]
