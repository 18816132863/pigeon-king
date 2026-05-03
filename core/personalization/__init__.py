"""
V157-V166 Personalization Learning Layer.

This package makes the personal operating agent increasingly user-shaped:
  V157 User Profile Model
  V158 Preference Rule Engine
  V159 Project Memory Registry
  V160 Relationship Context Map
  V161 Procedure Library
  V162 Decision Pattern Learner
  V163 Feedback Trainer
  V164 Personalization Drift Guard
  V165 Personalization Scorecard
  V166 Personalization Kernel
"""

from .schemas import (
    PreferenceStrength,
    FeedbackSignal,
    DriftLevel,
    PersonalizationStatus,
    UserProfile,
    PreferenceRule,
    ProjectMemory,
    RelationshipContext,
    ProcedureTemplate,
    DecisionPattern,
    FeedbackRecord,
    DriftGuardReport,
    PersonalizationScorecard,
    PersonalizationResult,
)
from .user_profile import UserProfileModel
from .preference_rules import PreferenceRuleEngine
from .project_memory import ProjectMemoryRegistry
from .relationship_context import RelationshipContextMap
from .procedure_library import ProcedureLibrary
from .decision_pattern_learner import DecisionPatternLearner
from .feedback_trainer import FeedbackTrainer
from .personalization_drift_guard import PersonalizationDriftGuard
from .personalization_scorecard import PersonalizationScorecardEngine
from .personalization_kernel import PersonalizationKernel, init_personalization, run_personalization_cycle

__all__ = [
    "PreferenceStrength",
    "FeedbackSignal",
    "DriftLevel",
    "PersonalizationStatus",
    "UserProfile",
    "PreferenceRule",
    "ProjectMemory",
    "RelationshipContext",
    "ProcedureTemplate",
    "DecisionPattern",
    "FeedbackRecord",
    "DriftGuardReport",
    "PersonalizationScorecard",
    "PersonalizationResult",
    "UserProfileModel",
    "PreferenceRuleEngine",
    "ProjectMemoryRegistry",
    "RelationshipContextMap",
    "ProcedureLibrary",
    "DecisionPatternLearner",
    "FeedbackTrainer",
    "PersonalizationDriftGuard",
    "PersonalizationScorecardEngine",
    "PersonalizationKernel",
    "init_personalization",
    "run_personalization_cycle",
]
