from pathlib import Path


def test_v137_command_bus(tmp_path: Path):
    from core.runtime_activation import CommandBus
    b = CommandBus(tmp_path)
    c = b.accept("继续推进版本")
    r = b.route(c)
    assert r.status.value == "routed"


def test_v138_api_facade(tmp_path: Path):
    from core.runtime_activation import ApiFacade
    r = ApiFacade(tmp_path).handle("/runtime/activate", body={"goal": "x"})
    assert r.status_code == 200


def test_v139_job_queue(tmp_path: Path):
    from core.runtime_activation import CommandBus, JobQueue
    c = CommandBus(tmp_path).accept("整理任务")
    q = JobQueue(tmp_path)
    q.enqueue(c)
    done = q.run_next()
    assert done.status.value == "completed"


def test_v140_scheduler_bridge(tmp_path: Path):
    from core.runtime_activation import CommandBus, JobQueue, SchedulerBridge
    c = CommandBus(tmp_path).accept("整理任务")
    j = JobQueue(tmp_path).enqueue(c)
    s = SchedulerBridge(tmp_path).create_once("run", j)
    assert s.status.value == "due"


def test_v141_state_inspector(tmp_path: Path):
    from core.runtime_activation import StateInspector
    (tmp_path / "core" / "runtime_activation").mkdir(parents=True)
    (tmp_path / "core" / "runtime_activation" / "__init__.py").write_text("", encoding="utf-8")
    r = StateInspector(tmp_path).inspect()
    assert r.status.value in {"warn", "fail", "pass"}


def test_v142_diagnostic_engine(tmp_path: Path):
    from core.runtime_activation import StateInspector, CompatibilityShim, DiagnosticEngine
    r = DiagnosticEngine().build(StateInspector(tmp_path).inspect(), CompatibilityShim(tmp_path).check())
    assert r.score >= 0


def test_v143_policy_simulator():
    from core.runtime_activation import PolicySimulator
    assert PolicySimulator().simulate("把 API token 发到群里").actual == "block"


def test_v144_artifact_packager(tmp_path: Path):
    from core.runtime_activation import ArtifactPackager
    (tmp_path / "core" / "runtime_activation").mkdir(parents=True)
    (tmp_path / "core" / "runtime_activation" / "x.py").write_text("x=1", encoding="utf-8")
    r = ArtifactPackager(tmp_path).build_record("pkg")
    assert r.status.value == "created"


def test_v145_compatibility_shim(tmp_path: Path):
    from core.runtime_activation import CompatibilityShim
    r = CompatibilityShim(tmp_path).check()
    assert r.status.value in {"compatible", "partial", "incompatible"}


def test_v146_runtime_activation_kernel(tmp_path: Path):
    from core.runtime_activation import RuntimeActivationKernel
    for layer in ["core/runtime_activation"]:
        (tmp_path / layer).mkdir(parents=True)
        (tmp_path / layer / "__init__.py").write_text("", encoding="utf-8")
    r = RuntimeActivationKernel(tmp_path, tmp_path / "state").run_cycle("整理任务")
    assert r.run_id
    assert r.api_status_code == 200
