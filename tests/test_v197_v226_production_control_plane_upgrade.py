from pathlib import Path


def test_v197_registry():
    from core.production_control_plane import SystemRegistry
    r = SystemRegistry().register()
    assert r.payload["count"] >= 10


def test_v199_access_matrix():
    from core.production_control_plane import RoleAccessMatrix
    r = RoleAccessMatrix().build()
    assert "owner" in r.payload["matrix"]


def test_v205_canary_controller():
    from core.production_control_plane import CanaryDeploymentController
    r = CanaryDeploymentController().evaluate(0.93, 0.01)
    assert r.status.value == "ready"


def test_v208_failover():
    from core.production_control_plane import ProviderFailoverController
    r = ProviderFailoverController().choose([{"name": "a", "healthy": False}, {"name": "b", "healthy": True, "latency": 100}])
    assert r.payload["primary"]["healthy"] is True


def test_v215_contract_tests():
    from core.production_control_plane import ContractTestRunner
    r = ContractTestRunner().run({"a": True, "b": True})
    assert r.status.value == "ready"


def test_v218_runbook_flow():
    from core.production_control_plane import PlaybookLibrary, RunbookExecutor
    p = PlaybookLibrary().get("release")
    r = RunbookExecutor().dry_run(p)
    assert r.payload["executed"]


def test_v220_training_curator():
    from core.production_control_plane import TrainingDataCurator
    r = TrainingDataCurator().curate([{"id": "1", "text": "ok"}, {"id": "2", "text": "token secret"}])
    assert r.status.value == "warn"


def test_v226_kernel(tmp_path: Path):
    from core.production_control_plane import run_production_control_plane_cycle
    r = run_production_control_plane_cycle("继续推进生产控制面", root=tmp_path)
    assert r.completed_versions == 30
    assert r.artifact_count >= 29
