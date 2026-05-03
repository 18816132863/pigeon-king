from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .schemas import OperationsIntelligenceResult, IntelligenceStatus, RiskLevel, new_id
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


class OperationsIntelligenceKernel:
    """V196: master operations intelligence orchestrator."""

    def __init__(self, root: str | Path = ".operations_intelligence_state"):
        self.root = Path(root)
        self.roadmap = RoadmapPlanner()
        self.portfolio = PortfolioManager()
        self.experiments = ExperimentDesigner()
        self.metrics = MetricsKPIEngine()
        self.ingestion = DataIngestionHub()
        self.quality = DataQualityGate()
        self.reporter = ReportGenerator()
        self.memo = DecisionMemoBuilder()
        self.risks = RiskRegister()
        self.incidents = IncidentManager()
        self.slo = SLOManager()
        self.cost = CostAnalyzer()
        self.performance = PerformanceProfiler()
        self.tokens = TokenOptimizer()
        self.policy = PromptPolicyCompiler()
        self.evaldata = EvalDatasetBuilder()
        self.ab = ABTestRunner()
        self.learning = ContinuousLearningQueue(root)
        self.freshness = KnowledgeFreshnessMonitor()
        self.compliance = ComplianceChecklistEngine()
        self.retention = DataRetentionManager()
        self.secrets = SecretRotationAdvisor()
        self.permissions = ConnectorPermissionReviewer()
        self.output_router = MultiChannelOutputRouter()
        self.briefing = StakeholderBriefingGenerator()
        self.release_notes = ReleaseNotesGenerator()
        self.audit = AuditExporter()
        self.dashboard = HealthDashboard()
        self.exec_summary = ExecutiveSummaryPackager()

    def run_cycle(self, goal: str) -> OperationsIntelligenceResult:
        run_id = new_id("opsintel")
        artifacts = []

        roadmap = self.roadmap.plan(goal, 167, 30); artifacts.append(roadmap)
        milestones = roadmap.payload["milestones"]
        artifacts.append(self.portfolio.build(milestones))
        artifacts.append(self.experiments.design(goal))
        artifacts.append(self.ingestion.ingest([
            {"id": "runtime_reports", "kind": "report", "records": 12, "trusted": True},
            {"id": "user_feedback", "kind": "feedback", "records": 5, "trusted": True},
            {"id": "external_notes", "kind": "note", "records": 2, "trusted": False},
        ]))
        artifacts.append(self.quality.evaluate(artifacts[-1]))
        artifacts.append(self.risks.register(goal, ["cost" if "30" in goal else "normal"]))
        artifacts.append(self.incidents.classify([]))
        artifacts.append(self.slo.define())
        artifacts.append(self.cost.analyze(token_estimate=30000 if "30" in goal else 8000, model_group="balanced"))
        artifacts.append(self.performance.profile(modules=30, files=40))
        artifacts.append(self.tokens.optimize([m["version"] + ":" + m["theme"] for m in milestones], budget=6000))
        artifacts.append(self.policy.compile(["压缩包", "一条命令", "不要一点点"], ["approval", "redaction"]))
        artifacts.append(self.evaldata.build())
        artifacts.append(self.ab.run({"quality": 0.88, "cost": 0.4}, {"quality": 0.92, "cost": 0.9}))
        artifacts.append(self.learning.enqueue("large version upgrades should ship as one package plus one command", "user_preference"))
        artifacts.append(self.freshness.assess("agent architecture", days_old=0))
        artifacts.append(self.compliance.build("agent"))
        artifacts.append(self.retention.policy("audit"))
        artifacts.append(self.secrets.advise(goal))
        artifacts.append(self.permissions.review([
            {"name": "email_send", "permissions": ["external_send"]},
            {"name": "file_read", "permissions": ["read"]},
            {"name": "plugin_install", "permissions": ["install"]},
        ]))
        artifacts.append(self.output_router.route("大龙虾", "upgrade_package"))
        artifacts.append(self.briefing.generate("technical_executor", ["V167-V196 complete", "run one command", "verify pass marker"]))
        artifacts.append(self.release_notes.generate("V167", "V196", [m["theme"] for m in milestones]))
        artifacts.append(self.audit.export([{"type": "upgrade", "message": goal}]))
        dashboard = self.dashboard.build({
            "roadmap": roadmap.status.value,
            "data_quality": artifacts[4].status.value,
            "risk": artifacts[5].status.value,
            "cost": artifacts[8].status.value,
            "secret": artifacts[18].status.value,
            "permission": artifacts[19].status.value,
        }); artifacts.append(dashboard)
        artifacts.append(self.reporter.generate("V167-V196 Operations Intelligence Report", artifacts))
        artifacts.append(self.memo.build("promote V167-V196", ["local verification passed", "package generated"], ["large_batch_change"]))
        artifacts.append(self.exec_summary.package("V167-V196 Operations Intelligence", dashboard.payload["summary"], ["apply zip", "run verify", "review warnings"]))
        metrics = self.metrics.compute(artifacts); artifacts.append(metrics)

        ready_count = sum(1 for a in artifacts if a.status == IntelligenceStatus.READY)
        warn_count = sum(1 for a in artifacts if a.status == IntelligenceStatus.WARN)
        blocked_count = sum(1 for a in artifacts if a.status == IntelligenceStatus.BLOCKED)
        readiness = round(sum(a.score for a in artifacts) / max(1, len(artifacts)), 4)

        risk_value = artifacts[5].payload.get("risk_level", RiskLevel.LOW.value)
        risk_level = RiskLevel(risk_value)

        if blocked_count:
            status = IntelligenceStatus.BLOCKED
            next_action = "先处理阻断项，再发布"
        elif warn_count:
            status = IntelligenceStatus.WARN
            next_action = "可覆盖执行，但需查看 warning 项"
        else:
            status = IntelligenceStatus.READY
            next_action = "可执行覆盖命令并跑验收脚本"

        return OperationsIntelligenceResult(
            run_id=run_id,
            goal=goal,
            status=status,
            completed_versions=30,
            artifact_count=len(artifacts),
            readiness_score=readiness,
            risk_level=risk_level,
            dashboard_summary=dashboard.payload["summary"],
            next_action=next_action,
            details={
                "ready_count": ready_count,
                "warn_count": warn_count,
                "blocked_count": blocked_count,
                "metrics": metrics.payload,
                "top_artifacts": [a.name for a in artifacts[:10]],
                "release_notes": artifacts[22].payload,
                "executive_summary": artifacts[-2].payload,
            },
        )


_DEFAULT: Optional[OperationsIntelligenceKernel] = None


def init_operations_intelligence(root: str | Path = ".operations_intelligence_state") -> Dict:
    global _DEFAULT
    _DEFAULT = OperationsIntelligenceKernel(root)
    return {"status": "ok", "root": str(Path(root)), "modules": 30}


def run_operations_intelligence_cycle(goal: str, root: str | Path = ".operations_intelligence_state") -> OperationsIntelligenceResult:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = OperationsIntelligenceKernel(root)
    return _DEFAULT.run_cycle(goal)
