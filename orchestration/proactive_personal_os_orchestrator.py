from __future__ import annotations

from typing import Any

from core.mission import MissionControlCenter
from core.multi_agent import RoleTeam
from core.verification import RollbackManager, AuditTrail
from infrastructure.capability_acquisition import SkillDiscoveryEngine
from infrastructure.connectors import ExternalConnectorRegistry, PermissionScopeManager
from memory_context.learning_loop.personal_evolution import PersonalFeedbackRouter, BehaviorPatternMiner, RiskToleranceCalibrator


class ProactivePersonalOSOrchestrator:
    """V10.3 high-level orchestrator.

    Combines mission control, role-team critique, capability discovery,
    connector planning, verification/rollback and personal evolution.
    """

    def __init__(self) -> None:
        self.mission = MissionControlCenter()
        self.team = RoleTeam()
        self.discovery = SkillDiscoveryEngine()
        self.connectors = ExternalConnectorRegistry()
        self.scope = PermissionScopeManager()
        self.rollback = RollbackManager()
        self.audit = AuditTrail()
        self.feedback = PersonalFeedbackRouter()
        self.patterns = BehaviorPatternMiner()
        self.risk = RiskToleranceCalibrator()

    def run(self, goal: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        mission = self.mission.build_mission(goal, context)
        team_review = self.team.review(mission)
        capability = None
        if any(n["node_type"] == "capability_acquisition" for n in mission["mission"]["nodes"]):
            capability = self.discovery.discover("solution_or_skill_gap")
        connector = self.connectors.register_planned("external_all_domain_connector", "mixed", ["read", "search"])
        scope = self.scope.evaluate(connector["scopes"])
        rollback = self.rollback.build_rollback_plan(mission["mission"]["nodes"])
        audit = self.audit.build_event("v10_3_orchestration", {"goal": goal, "mission_id": mission["mission"]["mission_id"]})
        personal = {
            "feedback_route": self.feedback.route_feedback({"goal": goal}),
            "patterns": self.patterns.mine([{"goal": goal}, context or {}]),
            "risk_tolerance": self.risk.calibrate([{"prefer": "auto"}]),
        }
        return {
            "status": "proactive_os_plan_ready",
            "shape": "Proactive Self-Extending Personal OS Agent",
            "mission": mission,
            "team_review": team_review,
            "capability_discovery": capability,
            "connector_plan": connector,
            "scope_policy": scope,
            "rollback_plan": rollback,
            "audit_event": audit,
            "personal_evolution": personal,
            "execution_allowed_now": team_review["allowed_to_execute"] and scope["status"] == "allowed_for_planning",
        }
