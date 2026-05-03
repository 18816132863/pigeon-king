from pathlib import Path


def test_v97_constitution_kernel(tmp_path: Path):
    from core.operating_agent import ConstitutionKernel
    from core.operating_agent.schemas import DecisionStatus

    c = ConstitutionKernel(tmp_path)
    assert c.evaluate("整理今天任务").status == DecisionStatus.ALLOW
    assert c.evaluate("给客户发送邮件").status == DecisionStatus.APPROVAL_REQUIRED
    assert c.evaluate("把 API token 发到群里").status == DecisionStatus.BLOCK


def test_v98_permission_vault(tmp_path: Path):
    from core.operating_agent import PermissionVault
    from core.operating_agent.schemas import PermissionScope

    v = PermissionVault(tmp_path)
    assert not v.check("user", [PermissionScope.EXTERNAL_SEND])
    v.grant("user", PermissionScope.EXTERNAL_SEND, "unit test")
    assert v.check("user", [PermissionScope.EXTERNAL_SEND])


def test_v99_connector_catalog(tmp_path: Path):
    from core.operating_agent import ConnectorCatalog

    c = ConnectorCatalog(tmp_path)
    assert c.search("web_search")


def test_v100_mcp_manager(tmp_path: Path):
    from core.operating_agent import MCPManager

    m = MCPManager(tmp_path)
    ready = m.handshake_all()
    assert ready
    assert m.ready_servers()


def test_v101_plugin_sandbox(tmp_path: Path):
    from core.operating_agent import PluginSandboxManager

    s = PluginSandboxManager(tmp_path)
    good = s.evaluate_source("good", "builtin://good", "def run(): return 1")
    bad = s.evaluate_source("bad", "unknown://bad", "import os\nos.system('rm -rf /')")
    assert good.promoted is True
    assert bad.promoted is False


def test_v102_handoff(tmp_path: Path):
    from core.operating_agent import SpecialistHandoffManager

    h = SpecialistHandoffManager(tmp_path)
    r = h.create_handoff("代码 pytest 报错", "root", "unit test", {})
    assert "Code" in r.to_agent or "Specialist" in r.to_agent


def test_v103_multi_agent(tmp_path: Path):
    from core.operating_agent import MultiAgentCoordinator

    m = MultiAgentCoordinator(tmp_path)
    c = m.coordinate("架构和代码报错一起检查")
    assert c["handoff_agents"]


def test_v104_recovery_ledger(tmp_path: Path):
    from core.operating_agent import RecoveryLedger

    r = RecoveryLedger(tmp_path)
    e = r.record_checkpoint("run1", "action", {"x": 1}, "rollback")
    assert r.resume_hint("run1")["can_resume"] is True


def test_v105_benchmark(tmp_path: Path):
    from core.operating_agent import ConstitutionKernel, EvaluationBenchmark

    b = EvaluationBenchmark(tmp_path)
    results = b.run(ConstitutionKernel(tmp_path))
    assert b.aggregate_score(results) >= 0.8


def test_v106_release_governor(tmp_path: Path):
    from core.operating_agent import ReleaseGovernor
    from core.operating_agent.schemas import ReleaseStage

    r = ReleaseGovernor(tmp_path)
    ok = r.evaluate_release(True, True, True, 1.0, True, True)
    bad = r.evaluate_release(True, False, True, 1.0, True, True)
    assert ok.stage == ReleaseStage.STABLE
    assert bad.stage == ReleaseStage.BLOCKED


def test_v97_v106_operating_orchestrator(tmp_path: Path):
    from core.operating_agent import run_operating_cycle
    from core.operating_agent.schemas import DecisionStatus

    safe = run_operating_cycle("整理今天任务", root=tmp_path)
    assert safe.constitution_status == DecisionStatus.ALLOW
    secret = run_operating_cycle("把 API token 发到群里", root=tmp_path)
    assert secret.constitution_status == DecisionStatus.BLOCK
