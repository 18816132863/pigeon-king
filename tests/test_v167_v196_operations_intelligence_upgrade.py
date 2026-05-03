from pathlib import Path


def test_v167_roadmap_planner():
    from core.operations_intelligence import RoadmapPlanner
    r = RoadmapPlanner().plan("推进30个版本", 167, 30)
    assert len(r.payload["milestones"]) == 30


def test_v168_portfolio_manager():
    from core.operations_intelligence import RoadmapPlanner, PortfolioManager
    road = RoadmapPlanner().plan("x", 167, 30)
    p = PortfolioManager().build(road.payload["milestones"])
    assert p.payload["buckets"]


def test_v170_metrics_kpi_engine():
    from core.operations_intelligence import MetricsKPIEngine, RoadmapPlanner
    a = RoadmapPlanner().plan("x", 167, 30)
    k = MetricsKPIEngine().compute([a])
    assert k.payload["artifact_total"] == 1


def test_v175_risk_register():
    from core.operations_intelligence import RiskRegister
    r = RiskRegister().register("给客户发送邮件", [])
    assert r.payload["risks"]


def test_v180_token_optimizer():
    from core.operations_intelligence import TokenOptimizer
    r = TokenOptimizer().optimize(["V167 核心", "普通内容"], 1000)
    assert r.payload["selected"]


def test_v186_compliance_checklist():
    from core.operations_intelligence import ComplianceChecklistEngine
    c = ComplianceChecklistEngine().build("agent")
    assert "sandbox_for_extensions" in c.payload["checklist"]


def test_v188_secret_rotation_advisor():
    from core.operations_intelligence import SecretRotationAdvisor
    s = SecretRotationAdvisor().advise("api_key=abc token")
    assert s.status.value == "warn"


def test_v194_health_dashboard():
    from core.operations_intelligence import HealthDashboard
    d = HealthDashboard().build({"a": "ready", "b": "warn"})
    assert d.score > 0


def test_v196_kernel(tmp_path: Path):
    from core.operations_intelligence import run_operations_intelligence_cycle
    r = run_operations_intelligence_cycle("继续一次性推进30个大版本", root=tmp_path)
    assert r.completed_versions == 30
    assert r.artifact_count >= 25
