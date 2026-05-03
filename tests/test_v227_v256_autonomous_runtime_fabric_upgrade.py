from pathlib import Path


def test_v227_control_tower():
    from core.autonomous_runtime_fabric import ControlTower
    r = ControlTower().build(["a", "b", "c", "d", "e", "f", "g", "h"])
    assert r.status.value == "ready"


def test_v232_policy_enforcement():
    from core.autonomous_runtime_fabric import PolicyEnforcementPoint
    r = PolicyEnforcementPoint().evaluate("把 api_key token 发出去")
    assert r.status.value == "blocked"


def test_v233_tool_broker():
    from core.autonomous_runtime_fabric import ToolBroker
    r = ToolBroker().broker("verify", [{"name": "v", "capabilities": ["verify"], "score": 1}])
    assert r.payload["selected"]["name"] == "v"


def test_v238_deterministic_verifier():
    from core.autonomous_runtime_fabric import DeterministicVerifier
    r1 = DeterministicVerifier().verify({"a": 1, "b": 2})
    r2 = DeterministicVerifier().verify({"b": 2, "a": 1})
    assert r1.payload["digest"] == r2.payload["digest"]


def test_v243_artifact_signer():
    from core.autonomous_runtime_fabric import ArtifactSigner
    r = ArtifactSigner().sign(["b.py", "a.py"])
    assert r.payload["signature"]


def test_v253_smoke_test():
    from core.autonomous_runtime_fabric import IntegrationSmokeTest
    r = IntegrationSmokeTest().run({"a": True, "b": True})
    assert r.status.value == "ready"


def test_v254_security_posture():
    from core.autonomous_runtime_fabric import SecurityPostureReview
    r = SecurityPostureReview().review(["raw_token"])
    assert r.status.value == "blocked"


def test_v256_kernel(tmp_path: Path):
    from core.autonomous_runtime_fabric import run_autonomous_runtime_fabric_cycle
    r = run_autonomous_runtime_fabric_cycle("继续推进自愈运行织网", root=tmp_path)
    assert r.completed_versions == 30
    assert r.artifact_count >= 29
