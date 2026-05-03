from __future__ import annotations

from core.continuous import ContinuousIntelligenceKernel, AttentionManager, RuntimeBudgetManager
from core.simulation import ScenarioSimulator
from core.knowledge import KnowledgeRefinery, SourceQualityEvaluator
from core.privacy import PrivacyBoundaryEngine
from infrastructure.ops import OpsHealthSupervisor, DriftDetector
from infrastructure.capability_lifecycle import CapabilityPromotionEngine, CapabilityRetirementPolicy
from memory_context.learning_loop.meta_learning import MetaLearningEngine, PromptStrategyOptimizer
from orchestration.continuous_personal_os_orchestrator import ContinuousPersonalOSOrchestrator


def test_continuous_kernel_proposes_initiative() -> None:
    result = ContinuousIntelligenceKernel().tick("继续推进", [{"priority": "high", "type": "goal"}])
    assert result["shape"] == "Continuous Intelligence Kernel"
    assert result["initiatives"]["initiatives"]


def test_attention_manager_interrupts_only_urgent() -> None:
    result = AttentionManager().rank([{"priority": "urgent"}])
    assert result["should_interrupt_user"] is True


def test_runtime_budget_has_zero_external_write_without_confirmation() -> None:
    budget = RuntimeBudgetManager().allocate()["budget"]
    assert budget["max_external_writes_without_confirmation"] == 0


def test_scenario_simulator_selects_path() -> None:
    result = ScenarioSimulator().simulate("接入外部能力")
    assert result["status"] == "simulation_ready"
    assert result["selected"]


def test_knowledge_refinery_accepts_trusted_source() -> None:
    result = KnowledgeRefinery().refine("goal", [{"type": "official_doc", "topic": "架构"}])
    assert result["accepted_count"] == 1


def test_source_quality_requires_cross_check_for_unknown() -> None:
    assert SourceQualityEvaluator().evaluate({"type": "unknown"})["requires_cross_check"] is True


def test_privacy_boundary_redacts_secret() -> None:
    result = PrivacyBoundaryEngine().prepare_external_payload({"goal": "x", "secret": "abc"}, ["goal", "secret"])
    assert result["payload"]["secret"] == "[REDACTED]"


def test_ops_supervisor_detects_no_drift() -> None:
    result = OpsHealthSupervisor().supervise({"a": 1}, {"a": 1}, [])
    assert result["drift"]["status"] == "stable"


def test_drift_detector_detects_change() -> None:
    assert DriftDetector().detect({"a": 1}, {"a": 2})["status"] == "drift_detected"


def test_capability_lifecycle_promotion_and_retirement() -> None:
    assert CapabilityPromotionEngine().promote({"sandboxed": True, "evidence_count": 6, "tests_passed": True})["status"] == "promotion_ready"
    assert CapabilityRetirementPolicy().evaluate({"failure_count": 0, "unused_days": 0})["status"] == "keep"


def test_meta_learning_prefers_direct_artifact() -> None:
    result = MetaLearningEngine().improve({"success": True}, {"directness": "high"})
    assert result["next_run_adjustment"] == "prefer_direct_complete_artifact"
    assert PromptStrategyOptimizer().optimize({"directness": "high"})["response_strategy"] == "direct_artifact_first"


def test_continuous_personal_os_orchestrator_shape() -> None:
    result = ContinuousPersonalOSOrchestrator().run("继续推进系统")
    assert result["shape"] == "Continuous Intelligence Personal OS Agent"
    assert result["execution_side_effect"] is False
