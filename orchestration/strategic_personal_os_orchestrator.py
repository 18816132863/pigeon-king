from __future__ import annotations

from typing import Any

from core.strategy import StrategicAutonomyCortex
from core.execution_contract import ExecutionContract, ExecutionReadinessGate
from core.portfolio import GoalPortfolioManager
from core.world_model import IntentState, EnvironmentState, UserContextGraph
from infrastructure.connector_factory import ConnectorBlueprintFactory
from memory_context.learning_loop.reflection import ReflectionEngine


class StrategicPersonalOSOrchestrator:
    """V10.4: strategic autonomy + execution contract + connector factory + reflection."""

    def __init__(self) -> None:
        self.strategy = StrategicAutonomyCortex()
        self.contract = ExecutionContract()
        self.gate = ExecutionReadinessGate()
        self.portfolio = GoalPortfolioManager()
        self.intent = IntentState()
        self.env = EnvironmentState()
        self.graph = UserContextGraph()
        self.connectors = ConnectorBlueprintFactory()
        self.reflection = ReflectionEngine()

    def run(self, goal: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        strategic = self.strategy.think(goal, context)
        intent = self.intent.parse(goal)
        env = self.env.snapshot(connected=context.get("connected", False), authorized_connectors=context.get("authorized_connectors"))
        user_graph = self.graph.build(context.get("user_facts", []))
        risk = strategic["evaluation"]["risk_level"]
        portfolio_goal = self.portfolio.add_goal(goal, horizon=context.get("horizon", "short"), risk_level=risk)
        portfolio = self.portfolio.snapshot()
        mission = {"mission_id": portfolio_goal["goal_id"], "goal": goal}
        contract = self.contract.build(mission, risk)
        readiness = self.gate.check(contract)
        blueprints = self.connectors.build_all_domain_blueprints()
        reflection = self.reflection.reflect(context.get("events", [{"status": "ok"}]))
        return {
            "status": "strategic_os_plan_ready",
            "shape": "Strategic Autonomous Personal OS Agent",
            "strategic": strategic,
            "intent": intent,
            "environment": env,
            "user_context_graph": user_graph,
            "portfolio": portfolio,
            "execution_contract": contract,
            "readiness": readiness,
            "connector_blueprints": blueprints,
            "reflection": reflection,
            "execution_allowed_now": readiness["status"] == "ready",
        }
