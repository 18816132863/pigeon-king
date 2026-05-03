from pathlib import Path


def test_v117_event_bus(tmp_path: Path):
    from core.operating_spine import EventBus
    b = EventBus(tmp_path)
    b.publish("run1", "topic", "message")
    assert b.count("run1") == 1


def test_v118_state_migration(tmp_path: Path):
    from core.operating_spine import StateMigrationManager
    m = StateMigrationManager(tmp_path)
    rec = m.plan("V1", "V2", ["missing_file.py"])
    applied = m.apply(rec)
    assert applied.status.value == "applied"


def test_v119_capability_contracts(tmp_path: Path):
    from core.operating_spine import CapabilityContractRegistry
    c = CapabilityContractRegistry(tmp_path)
    assert c.validate_all()


def test_v120_task_runtime(tmp_path: Path):
    from core.operating_spine import TaskRuntimeAdapter
    r = TaskRuntimeAdapter(tmp_path).run_dry("给客户发送邮件")
    assert any(x.status.value == "waiting_approval" for x in r)


def test_v121_approval_recovery(tmp_path: Path):
    from core.operating_spine import ApprovalRecoveryWorkflow
    p = ApprovalRecoveryWorkflow(tmp_path).build("send email", True)
    assert p.status.value == "waiting"


def test_v122_connector_health(tmp_path: Path):
    from core.operating_spine import ConnectorHealthMonitor
    h = ConnectorHealthMonitor(tmp_path).check("x", latency_ms=6000, failure_rate=0.1)
    assert h.status.value == "offline"


def test_v123_memory_consolidation(tmp_path: Path):
    from core.operating_spine import MemoryConsolidator
    r = MemoryConsolidator(tmp_path).consolidate([{"kind": "preference"}, {"kind": "episode"}])
    assert r.after_count == 2


def test_v124_skill_lifecycle(tmp_path: Path):
    from core.operating_spine import SkillLifecycleManager
    s = SkillLifecycleManager(tmp_path)
    r = s.propose("demo", "1.0")
    r = s.canary(r.id, 0.95)
    assert r.status.value == "active"


def test_v125_scenario_harness(tmp_path: Path):
    from core.operating_spine import ScenarioHarness
    h = ScenarioHarness(tmp_path)
    results = h.run_default_suite({"contract_ready": True, "runtime_ready": True, "scenario_passed": True})
    assert results


def test_v126_operating_spine(tmp_path: Path):
    from core.operating_spine import run_operating_spine_cycle
    from core.operating_spine.schemas import SpineStatus
    r = run_operating_spine_cycle("把 API token 发到群里", root=tmp_path)
    assert r.status == SpineStatus.BLOCKED
