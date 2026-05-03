# -*- coding: utf-8 -*-
"""V86 personal execution agent orchestrator."""
from __future__ import annotations

from typing import Any, Dict, Iterable

from .durable_task_state import DurableTaskState
from .execution_planner import ExecutionPlanner
from .experience_writer import ExperienceWriter
from .goal_compiler import GoalCompiler
from .policy_judge import PolicyJudge
from .result_verifier import ResultVerifier
from .schemas import TaskGraph
from .task_graph import TaskGraphBuilder, TaskGraphExecutor


class PersonalExecutionAgent:
    def __init__(self, state_root: str = ".v86_state"):
        self.goal_compiler = GoalCompiler()
        self.policy_judge = PolicyJudge()
        self.graph_builder = TaskGraphBuilder(self.policy_judge)
        self.planner = ExecutionPlanner()
        self.executor = TaskGraphExecutor()
        self.state = DurableTaskState(state_root)
        self.verifier = ResultVerifier()
        self.experience_writer = ExperienceWriter(f"{state_root}/experience.jsonl")

    def prepare(self, request: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        goal = self.goal_compiler.compile(request, context=context)
        graph = self.graph_builder.build(goal)
        plan = self.planner.plan(graph, context=context)
        self.state.save_graph(graph)
        return {"goal": goal.to_dict(), "graph": graph.to_dict(), "plan": plan.to_dict()}

    def run(self, request: str, context: Dict[str, Any] | None = None, approvals: Iterable[str] | None = None, execute_low_risk: bool = True) -> Dict[str, Any]:
        goal = self.goal_compiler.compile(request, context=context)
        graph = self.graph_builder.build(goal)
        plan = self.planner.plan(graph, context=context)
        graph = self.executor.run_safe(graph, approvals=approvals, execute_low_risk=execute_low_risk)
        self.state.save_graph(graph)
        verification = self.verifier.verify(graph)
        experience = self.experience_writer.write(graph, verification)
        self.state.append_event(graph.graph_id, "verification", verification.to_dict())
        self.state.append_event(graph.graph_id, "experience_written", experience.to_dict())
        return {
            "status": "prepared_with_safe_execution",
            "goal": goal.to_dict(),
            "graph": graph.to_dict(),
            "plan": plan.to_dict(),
            "execution_summary": self.executor.summary(graph),
            "verification": verification.to_dict(),
            "experience": experience.to_dict(),
        }

    def resume(self, graph_id: str, approvals: Iterable[str] | None = None, execute_low_risk: bool = True) -> Dict[str, Any]:
        graph = self.state.load_graph(graph_id)
        graph = self.executor.run_safe(graph, approvals=approvals, execute_low_risk=execute_low_risk)
        self.state.save_graph(graph)
        verification = self.verifier.verify(graph)
        experience = self.experience_writer.write(graph, verification)
        return {
            "status": "resumed",
            "graph": graph.to_dict(),
            "execution_summary": self.executor.summary(graph),
            "verification": verification.to_dict(),
            "experience": experience.to_dict(),
        }


def compile_goal(request: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return GoalCompiler().compile(request, context=context).to_dict()


def build_task_graph(request: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    goal = GoalCompiler().compile(request, context=context)
    return TaskGraphBuilder().build(goal).to_dict()


def run_personal_execution(request: str, context: Dict[str, Any] | None = None, approvals: Iterable[str] | None = None) -> Dict[str, Any]:
    return PersonalExecutionAgent().run(request, context=context, approvals=approvals)
