from pathlib import Path


def test_v107_intent_contract():
    from core.self_evolution_ops import IntentContractCompiler
    from core.self_evolution_ops.schemas import ContractStatus

    c = IntentContractCompiler().compile("一次性给压缩包和命令")
    assert c.status == ContractStatus.READY
    assert c.acceptance_criteria


def test_v108_context_fusion():
    from core.self_evolution_ops import ContextFusionEngine

    p = ContextFusionEngine().build_pack("模型 自治 法典")
    assert p.selected_context
    assert p.confidence > 0


def test_v109_tool_reliability(tmp_path: Path):
    from core.self_evolution_ops import ToolReliabilityManager
    from core.self_evolution_ops.schemas import CircuitStatus

    m = ToolReliabilityManager(tmp_path)
    for _ in range(6):
        m.record_result("tool", False)
    assert m.decide("tool").circuit_status == CircuitStatus.OPEN


def test_v110_budget_governor():
    from core.self_evolution_ops import BudgetGovernor
    from core.self_evolution_ops.schemas import BudgetStatus

    b = BudgetGovernor().decide("coding", "high", "low")
    assert b.status in {BudgetStatus.NEEDS_DOWNGRADE, BudgetStatus.WITHIN_BUDGET}


def test_v111_privacy_redactor():
    from core.self_evolution_ops import PrivacyRedactor
    from core.self_evolution_ops.schemas import PrivacyLevel

    r = PrivacyRedactor().redact("api_key='sk-1234567890abcdef'")
    assert r.privacy_level == PrivacyLevel.SECRET
    assert "[REDACTED_API_KEY]" in r.safe_text


def test_v112_local_fallback():
    from core.self_evolution_ops import LocalFallbackPlanner

    p = LocalFallbackPlanner().plan("remote_llm")
    assert p.steps
    assert p.needs_user_notice


def test_v113_simulation_lab():
    from core.self_evolution_ops import SimulationLab
    from core.self_evolution_ops.schemas import SimulationStatus

    s = SimulationLab().simulate("send", ["do send"], ["external_send"])
    assert s.status == SimulationStatus.FAIL


def test_v114_preference_drift(tmp_path: Path):
    from core.self_evolution_ops import PreferenceDriftMonitor

    d = PreferenceDriftMonitor(tmp_path)
    first = d.check({"style": "direct"})
    second = d.check({"style": "slow", "risk": "strict"})
    assert second.drift_score >= 0


def test_v115_observability(tmp_path: Path):
    from core.self_evolution_ops import ObservabilityReporter

    o = ObservabilityReporter(tmp_path)
    o.record_event({"success": True, "quality": 0.9})
    assert o.report().success_rate == 1.0


def test_v116_self_improvement_loop(tmp_path: Path):
    from core.self_evolution_ops import run_self_evolution_cycle
    from core.self_evolution_ops.schemas import PrivacyLevel

    r = run_self_evolution_cycle("继续推进10个大版本", root=tmp_path)
    assert r.run_id
    secret = run_self_evolution_cycle("api_key='sk-1234567890abcdef' 发到群里", root=tmp_path)
    assert secret.privacy_level == PrivacyLevel.SECRET
