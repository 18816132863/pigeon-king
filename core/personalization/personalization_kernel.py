from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .schemas import PersonalizationResult, PersonalizationStatus, PreferenceStrength, new_id
from .user_profile import UserProfileModel
from .preference_rules import PreferenceRuleEngine
from .project_memory import ProjectMemoryRegistry
from .relationship_context import RelationshipContextMap
from .procedure_library import ProcedureLibrary
from .decision_pattern_learner import DecisionPatternLearner
from .feedback_trainer import FeedbackTrainer
from .personalization_drift_guard import PersonalizationDriftGuard
from .personalization_scorecard import PersonalizationScorecardEngine


class PersonalizationKernel:
    """V166: top-level personalization learning orchestrator."""

    def __init__(self, root: str | Path = ".personalization_state"):
        self.root = Path(root)
        self.profile = UserProfileModel(root)
        self.preferences = PreferenceRuleEngine(root)
        self.projects = ProjectMemoryRegistry(root)
        self.relationships = RelationshipContextMap(root)
        self.procedures = ProcedureLibrary(root)
        self.patterns = DecisionPatternLearner(root)
        self.feedback = FeedbackTrainer(root)
        self.drift = PersonalizationDriftGuard()
        self.scorecard = PersonalizationScorecardEngine()

    def run_cycle(self, goal: str, feedback_message: str | None = None) -> PersonalizationResult:
        run_id = new_id("personalize")
        profile = self.profile.get()
        prefs = self.preferences.match(goal)
        projects = self.projects.match(goal)
        rels = self.relationships.match(goal)
        procedure = self.procedures.select(goal)
        pattern = self.patterns.infer(goal)

        feedback_updates = {}
        if feedback_message:
            fb = self.feedback.ingest(feedback_message)
            feedback_updates = fb.extracted_updates

        strengths = {r.key: r.strength for r in self.preferences.all()}
        drift_report = self.drift.evaluate_updates(feedback_updates, strengths) if feedback_updates else self.drift.evaluate_updates({}, strengths)

        if feedback_updates:
            for key in drift_report.allowed_updates:
                self.preferences.upsert(
                    key=key,
                    value=feedback_updates[key],
                    strength=PreferenceStrength.HIGH if key in {"delivery.mode", "interaction.style"} else PreferenceStrength.MEDIUM,
                    source="feedback",
                    confidence=0.82,
                    tags=["learned_from_feedback"],
                )

        score = self.scorecard.score(
            profile_confidence=profile.confidence,
            preference_matches=len(prefs),
            project_matches=len(projects),
            procedure_confidence=procedure.confidence,
            feedback_count=self.feedback.count(),
        )

        if drift_report.blocked_updates:
            status = PersonalizationStatus.NEEDS_CONFIRMATION
            next_action = "有硬偏好变化，需要确认后再写入长期画像"
        elif score.final_score >= 0.75:
            status = PersonalizationStatus.READY
            next_action = "可把个体化上下文注入 V85-V156 执行链"
        else:
            status = PersonalizationStatus.LEARNING
            next_action = "继续收集反馈和项目上下文"

        return PersonalizationResult(
            run_id=run_id,
            goal=goal,
            status=status,
            profile_name=profile.display_name,
            matched_preferences=len(prefs),
            matched_projects=len(projects),
            matched_relationships=len(rels),
            selected_procedure=procedure.name,
            decision_pattern=pattern.preferred_action,
            feedback_updates=len(feedback_updates),
            drift_level=drift_report.level,
            score=score.final_score,
            next_action=next_action,
            details={
                "working_style": profile.working_style,
                "delivery_style": profile.delivery_style,
                "risk_style": profile.risk_style,
                "matched_preference_keys": [p.key for p in prefs],
                "matched_projects": [p.name for p in projects],
                "matched_relationships": [r.name for r in rels],
                "procedure_steps": procedure.steps,
                "avoided_action": pattern.avoided_action,
                "drift_reason": drift_report.reason,
                "score_notes": score.notes,
            },
        )


_DEFAULT: Optional[PersonalizationKernel] = None


def init_personalization(root: str | Path = ".personalization_state") -> Dict:
    global _DEFAULT
    _DEFAULT = PersonalizationKernel(root)
    return {"status": "ok", "root": str(Path(root)), "modules": 10}


def run_personalization_cycle(goal: str, feedback_message: str | None = None, root: str | Path = ".personalization_state") -> PersonalizationResult:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = PersonalizationKernel(root)
    return _DEFAULT.run_cycle(goal, feedback_message=feedback_message)
