from __future__ import annotations

from .schemas import PersonalizationScorecard, new_id


class PersonalizationScorecardEngine:
    """V165: scores personalization readiness."""

    def score(
        self,
        profile_confidence: float,
        preference_matches: int,
        project_matches: int,
        procedure_confidence: float,
        feedback_count: int,
    ) -> PersonalizationScorecard:
        profile_score = min(1.0, profile_confidence)
        preference_score = min(1.0, preference_matches / 3)
        project_score = min(1.0, project_matches / 2)
        procedure_score = min(1.0, procedure_confidence)
        feedback_score = min(1.0, feedback_count / 10)
        final = round(profile_score * 0.25 + preference_score * 0.25 + project_score * 0.15 + procedure_score * 0.25 + feedback_score * 0.10, 4)
        notes = []
        if final < 0.75:
            notes.append("personalization needs more feedback and project context")
        else:
            notes.append("personalization ready for governed execution")
        return PersonalizationScorecard(
            id=new_id("pscore"),
            profile_score=profile_score,
            preference_score=preference_score,
            project_score=project_score,
            procedure_score=procedure_score,
            feedback_score=feedback_score,
            final_score=final,
            notes=notes,
        )
