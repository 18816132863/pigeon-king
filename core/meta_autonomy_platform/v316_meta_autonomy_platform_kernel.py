from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional

from .schemas import MetaPlatformResult, PlatformStatus, PlatformGate, PlatformSeverity, new_id
from .v257_capability_marketplace import CapabilityMarketplace
from .v258_skill_composer import SkillComposer
from .v259_workflow_compiler import WorkflowCompiler
from .v260_decision_graph_optimizer import DecisionGraphOptimizer
from .v261_intent_cache import IntentCache
from .v262_semantic_router import SemanticRouter
from .v263_task_batcher import TaskBatcher
from .v264_priority_queue_planner import PriorityQueuePlanner
from .v265_parallel_plan_simulator import ParallelPlanSimulator
from .v266_state_consistency_checker import StateConsistencyChecker
from .v267_isolation_boundary_checker import IsolationBoundaryChecker
from .v268_policy_diff_engine import PolicyDiffEngine
from .v269_approval_sla_planner import ApprovalSLAPlanner
from .v270_credential_hygiene_scanner import CredentialHygieneScanner
from .v271_prompt_firewall import PromptFirewall
from .v272_tool_allowlist_compiler import ToolAllowlistCompiler
from .v273_data_minimization_engine import DataMinimizationEngine
from .v274_context_deduplicator import ContextDeduplicator
from .v275_memory_conflict_resolver import MemoryConflictResolver
from .v276_knowledge_graph_index import KnowledgeGraphIndex
from .v277_ontology_mapper import OntologyMapper
from .v278_retrieval_strategy_tuner import RetrievalStrategyTuner
from .v279_source_credibility_scorer import SourceCredibilityScorer
from .v280_evidence_linker import EvidenceLinker
from .v281_artifact_dependency_packager import ArtifactDependencyPackager
from .v282_patch_conflict_resolver import PatchConflictResolver
from .v283_schema_evolution_planner import SchemaEvolutionPlanner
from .v284_migration_dry_run_engine import MigrationDryRunEngine
from .v285_compatibility_matrix_builder import CompatibilityMatrixBuilder
from .v286_device_capability_matcher import DeviceCapabilityMatcher
from .v287_local_executor_planner import LocalExecutorPlanner
from .v288_remote_executor_planner import RemoteExecutorPlanner
from .v289_sandbox_fleet_manager import SandboxFleetManager
from .v290_runtime_contract_broker import RuntimeContractBroker
from .v291_operation_idempotency_guard import OperationIdempotencyGuard
from .v292_side_effect_reconciliation import SideEffectReconciliation
from .v293_human_checkpoint_orchestrator import HumanCheckpointOrchestrator
from .v294_audit_trail_compressor import AuditTrailCompressor
from .v295_observability_correlation_engine import ObservabilityCorrelationEngine
from .v296_token_budget_allocator import TokenBudgetAllocator
from .v297_cost_center_allocator import CostCenterAllocator
from .v298_latency_budget_planner import LatencyBudgetPlanner
from .v299_throughput_controller import ThroughputController
from .v300_concurrency_governor import ConcurrencyGovernor
from .v301_adaptive_rate_limiter import AdaptiveRateLimiter
from .v302_load_shedding_controller import LoadSheddingController
from .v303_regression_risk_predictor import RegressionRiskPredictor
from .v304_quality_drift_detector import QualityDriftDetector
from .v305_agent_maturity_assessor import AgentMaturityAssessor
from .v306_roadmap_reprioritizer import RoadmapReprioritizer
from .v307_technical_debt_register import TechnicalDebtRegister
from .v308_deprecation_manager import DeprecationManager
from .v309_user_journey_tracer import UserJourneyTracer
from .v310_stakeholder_alignment_matrix import StakeholderAlignmentMatrix
from .v311_operator_training_packager import OperatorTrainingPackager
from .v312_runbook_quality_scorer import RunbookQualityScorer
from .v313_model_quality_arbiter import ModelQualityArbiter
from .v314_vendor_governance_registry import VendorGovernanceRegistry
from .v315_platform_certification_board import PlatformCertificationBoard

class MetaAutonomyPlatformKernel:
    """V316: master kernel for V257-V316 meta autonomy platform."""

    def __init__(self, root: str | Path = ".meta_autonomy_platform_state"):
        self.root = Path(root)
        self.features = [
            CapabilityMarketplace(),
            SkillComposer(),
            WorkflowCompiler(),
            DecisionGraphOptimizer(),
            IntentCache(),
            SemanticRouter(),
            TaskBatcher(),
            PriorityQueuePlanner(),
            ParallelPlanSimulator(),
            StateConsistencyChecker(),
            IsolationBoundaryChecker(),
            PolicyDiffEngine(),
            ApprovalSLAPlanner(),
            CredentialHygieneScanner(),
            PromptFirewall(),
            ToolAllowlistCompiler(),
            DataMinimizationEngine(),
            ContextDeduplicator(),
            MemoryConflictResolver(),
            KnowledgeGraphIndex(),
            OntologyMapper(),
            RetrievalStrategyTuner(),
            SourceCredibilityScorer(),
            EvidenceLinker(),
            ArtifactDependencyPackager(),
            PatchConflictResolver(),
            SchemaEvolutionPlanner(),
            MigrationDryRunEngine(),
            CompatibilityMatrixBuilder(),
            DeviceCapabilityMatcher(),
            LocalExecutorPlanner(),
            RemoteExecutorPlanner(),
            SandboxFleetManager(),
            RuntimeContractBroker(),
            OperationIdempotencyGuard(),
            SideEffectReconciliation(),
            HumanCheckpointOrchestrator(),
            AuditTrailCompressor(),
            ObservabilityCorrelationEngine(),
            TokenBudgetAllocator(),
            CostCenterAllocator(),
            LatencyBudgetPlanner(),
            ThroughputController(),
            ConcurrencyGovernor(),
            AdaptiveRateLimiter(),
            LoadSheddingController(),
            RegressionRiskPredictor(),
            QualityDriftDetector(),
            AgentMaturityAssessor(),
            RoadmapReprioritizer(),
            TechnicalDebtRegister(),
            DeprecationManager(),
            UserJourneyTracer(),
            StakeholderAlignmentMatrix(),
            OperatorTrainingPackager(),
            RunbookQualityScorer(),
            ModelQualityArbiter(),
            VendorGovernanceRegistry(),
            PlatformCertificationBoard()
        ]

    def _context(self, goal: str) -> dict:
        lower = goal.lower()
        sensitive = any(x in lower for x in ["token", "secret", "api_key", "password"]) or any(x in goal for x in ["密钥", "密码"])
        high_risk = any(x in goal for x in ["发送", "删除", "安装", "转账", "付款", "客户", "外部"])
        large_batch = any(x in goal for x in ["60", "六十", "很多", "大量", "一次多", "不够多", "批量"])
        return {"goal": goal, "sensitive": sensitive, "high_risk": high_risk, "large_batch": large_batch}

    def run_cycle(self, goal: str) -> MetaPlatformResult:
        run_id = new_id("metaplatform")
        context = self._context(goal)
        artifacts = [feature.process(context) for feature in self.features]

        # Add final kernel artifact as V316.
        blocked_count = sum(1 for a in artifacts if a.status == PlatformStatus.BLOCKED)
        warn_count = sum(1 for a in artifacts if a.status == PlatformStatus.WARN)
        learning_count = sum(1 for a in artifacts if a.status == PlatformStatus.LEARNING)
        avg_before = sum(a.score for a in artifacts) / max(1, len(artifacts))
        kernel_status = PlatformStatus.BLOCKED if blocked_count else (PlatformStatus.WARN if warn_count else PlatformStatus.READY)
        kernel_score = round(max(0.0, min(1.0, avg_before)), 4)

        from .schemas import PlatformArtifact
        kernel_artifact = PlatformArtifact(
            id=new_id("platform"),
            version="V316",
            name="超大规模自治平台总控",
            kind="meta_autonomy_platform_kernel",
            status=kernel_status,
            score=kernel_score,
            payload={
                "orchestrated_features": len(artifacts),
                "blocked_count": blocked_count,
                "warn_count": warn_count,
                "learning_count": learning_count,
                "context": context,
            },
        )
        artifacts.append(kernel_artifact)

        readiness = round(sum(a.score for a in artifacts) / max(1, len(artifacts)), 4)
        blocked_count = sum(1 for a in artifacts if a.status == PlatformStatus.BLOCKED)
        warn_count = sum(1 for a in artifacts if a.status == PlatformStatus.WARN)
        learning_count = sum(1 for a in artifacts if a.status == PlatformStatus.LEARNING)

        if blocked_count:
            status = PlatformStatus.BLOCKED
            gate = PlatformGate.FAIL
            severity = PlatformSeverity.CRITICAL if context["sensitive"] else PlatformSeverity.HIGH
            next_action = "先处理 blocked 项，尤其是敏感信息/密钥/外部副作用"
        elif warn_count:
            status = PlatformStatus.WARN
            gate = PlatformGate.WARN
            severity = PlatformSeverity.MEDIUM
            next_action = "可覆盖执行，但需要查看 warning 项并保留验收/回滚"
        else:
            status = PlatformStatus.READY
            gate = PlatformGate.PASS
            severity = PlatformSeverity.LOW
            next_action = "可执行覆盖命令并跑验收脚本"

        summary = f"meta_platform={status.value}, readiness={readiness}, artifacts={len(artifacts)}, warnings={warn_count}, blocked={blocked_count}, learning={learning_count}"

        return MetaPlatformResult(
            run_id=run_id,
            goal=goal,
            status=status,
            completed_versions=60,
            artifact_count=len(artifacts),
            readiness_score=readiness,
            gate=gate,
            severity=severity,
            dashboard_summary=summary,
            next_action=next_action,
            details={
                "ready_count": sum(1 for a in artifacts if a.status == PlatformStatus.READY),
                "warn_count": warn_count,
                "blocked_count": blocked_count,
                "learning_count": learning_count,
                "top_artifacts": [a.name for a in artifacts[:15]],
                "blocked_artifacts": [a.name for a in artifacts if a.status == PlatformStatus.BLOCKED],
                "warning_artifacts": [a.name for a in artifacts if a.status == PlatformStatus.WARN][:20],
                "learning_artifacts": [a.name for a in artifacts if a.status == PlatformStatus.LEARNING][:20],
            },
        )


_DEFAULT: Optional[MetaAutonomyPlatformKernel] = None


def init_meta_autonomy_platform(root: str | Path = ".meta_autonomy_platform_state") -> Dict:
    global _DEFAULT
    _DEFAULT = MetaAutonomyPlatformKernel(root)
    return {"status": "ok", "root": str(Path(root)), "modules": 60}


def run_meta_autonomy_platform_cycle(goal: str, root: str | Path = ".meta_autonomy_platform_state") -> MetaPlatformResult:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = MetaAutonomyPlatformKernel(root)
    return _DEFAULT.run_cycle(goal)
