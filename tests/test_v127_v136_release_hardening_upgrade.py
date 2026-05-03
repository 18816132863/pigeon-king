from pathlib import Path


def test_v127_environment_doctor(tmp_path: Path):
    from core.release_hardening import EnvironmentDoctor
    (tmp_path / "core").mkdir()
    (tmp_path / "agent_kernel").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    r = EnvironmentDoctor(tmp_path).check()
    assert r.status.value == "pass"


def test_v128_config_contract(tmp_path: Path):
    from core.release_hardening import ConfigContractManager
    r = ConfigContractManager(tmp_path).evaluate(required_env=[])
    assert r.status.value == "pass"


def test_v129_dependency_guard(tmp_path: Path):
    from core.release_hardening import DependencyGuard
    d = DependencyGuard(tmp_path)
    results = d.check_all(["json", "pathlib"])
    assert d.overall_status(results).value == "pass"


def test_v130_snapshot_manager(tmp_path: Path):
    from core.release_hardening import SnapshotManager
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "x.py").write_text("x=1", encoding="utf-8")
    r = SnapshotManager(tmp_path, tmp_path / "state").create_manifest()
    assert r.tracked_files == 1


def test_v131_rollback_manager(tmp_path: Path):
    from core.release_hardening import SnapshotManager, RollbackManager
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "x.py").write_text("x=1", encoding="utf-8")
    s = SnapshotManager(tmp_path, tmp_path / "state").create_manifest()
    p = RollbackManager().build_plan(s)
    assert p.commands


def test_v132_regression_matrix():
    from core.release_hardening import RegressionMatrix
    r = RegressionMatrix().run()
    assert r.status.value == "pass"


def test_v133_release_manifest(tmp_path: Path):
    from core.release_hardening import ReleaseManifestBuilder
    (tmp_path / "core" / "release_hardening").mkdir(parents=True)
    (tmp_path / "core" / "release_hardening" / "x.py").write_text("x=1", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "v127_v136_x.py").write_text("x=1", encoding="utf-8")
    m = ReleaseManifestBuilder(tmp_path).build()
    assert m.status.value == "pass"


def test_v134_deployment_profile():
    from core.release_hardening import DeploymentProfileManager
    from core.release_hardening.schemas import ProfileName
    p = DeploymentProfileManager().build(ProfileName.PROD, regression_pass=True, snapshot_ready=True)
    assert p.gate_status.value == "warn"


def test_v135_runtime_report():
    from core.release_hardening import RuntimeReporter
    r = RuntimeReporter().build("r1", {"a": "pass", "b": "pass"})
    assert r.status.value == "ready"


def test_v136_release_hardening_kernel(tmp_path: Path):
    from core.release_hardening import ReleaseHardeningKernel
    from core.release_hardening.schemas import ProfileName
    for d in ["core", "agent_kernel", "scripts", "tests"]:
        (tmp_path / d).mkdir()
    r = ReleaseHardeningKernel(tmp_path, tmp_path / "state").run_cycle("release", ProfileName.LOCAL)
    assert r.run_id
    assert r.regression_status.value == "pass"
