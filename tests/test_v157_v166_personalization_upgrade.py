from pathlib import Path


def test_v157_user_profile(tmp_path: Path):
    from core.personalization import UserProfileModel
    p = UserProfileModel(tmp_path).get()
    assert p.delivery_style


def test_v158_preference_rules(tmp_path: Path):
    from core.personalization import PreferenceRuleEngine
    r = PreferenceRuleEngine(tmp_path).match("继续推进版本给压缩包和命令")
    assert len(r) >= 2


def test_v159_project_memory(tmp_path: Path):
    from core.personalization import ProjectMemoryRegistry
    r = ProjectMemoryRegistry(tmp_path).match("小艺架构版本推进")
    assert r


def test_v160_relationship_context(tmp_path: Path):
    from core.personalization import RelationshipContextMap
    r = RelationshipContextMap(tmp_path).match("给大龙虾一条命令")
    assert r


def test_v161_procedure_library(tmp_path: Path):
    from core.personalization import ProcedureLibrary
    p = ProcedureLibrary(tmp_path).select("继续推进版本")
    assert p.name == "one_shot_upgrade_package"


def test_v162_decision_pattern(tmp_path: Path):
    from core.personalization import DecisionPatternLearner
    p = DecisionPatternLearner(tmp_path).infer("发送邮件")
    assert p.preferred_action == "dry_run_and_approval"


def test_v163_feedback_trainer(tmp_path: Path):
    from core.personalization import FeedbackTrainer
    r = FeedbackTrainer(tmp_path).ingest("不要一点点改，给压缩包和命令")
    assert r.extracted_updates


def test_v164_drift_guard():
    from core.personalization import PersonalizationDriftGuard
    from core.personalization.schemas import PreferenceStrength, DriftLevel
    r = PersonalizationDriftGuard().evaluate_updates({"risk.high_risk": "auto_execute"}, {"risk.high_risk": PreferenceStrength.HARD})
    assert r.level == DriftLevel.NEEDS_CONFIRMATION


def test_v165_scorecard():
    from core.personalization import PersonalizationScorecardEngine
    s = PersonalizationScorecardEngine().score(0.8, 3, 2, 0.9, 5)
    assert s.final_score >= 0.75


def test_v166_personalization_kernel(tmp_path: Path):
    from core.personalization import run_personalization_cycle
    r = run_personalization_cycle("继续推进十个大版本并给压缩包和命令", root=tmp_path)
    assert r.selected_procedure == "one_shot_upgrade_package"
