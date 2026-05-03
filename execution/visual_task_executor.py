"""
V1.0 Visual Task Executor Bridge

Bridges VisualPlanner + ActionExecutor into the main execution pipeline.
Provides a single entry point for GUI-based tasks.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class VisualTaskResult:
    task_id: str
    goal: str
    plan_steps: int
    executed_steps: int
    success: bool
    errors: List[str]
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class VisualTaskExecutor:
    """Execute GUI tasks through VisualPlanner + ActionExecutor.

    Combines planning (VisualPlanner) and execution (ActionExecutor)
    into a single callable interface that can be integrated into
    PersonalOperatingLoopV2.

    Usage:
        executor = VisualTaskExecutor()
        result = executor.run("打开微信搜索张三")
    """

    def __init__(self, tool_executor=None):
        self._planner = None
        self._executor = None
        self._observer = None
        self._tool_executor = tool_executor  # xiaoyi_gui_agent or mock

    def _get_planner(self):
        if self._planner is None:
            from execution.visual_operation_agent import VisualPlanner
            self._planner = VisualPlanner()
        return self._planner

    def _get_executor(self):
        if self._executor is None:
            from execution.visual_operation_agent import ActionExecutor
            self._executor = ActionExecutor(tool_executor=self._tool_executor)
        return self._executor

    def _get_observer(self):
        if self._observer is None:
            from execution.visual_operation_agent import ScreenObserver
            self._observer = ScreenObserver()
        return self._observer

    def plan(self, goal: str, app_name: str = "") -> List[Dict[str, Any]]:
        """Plan visual steps without executing."""
        planner = self._get_planner()
        steps = planner.plan_for_goal(goal, app_name=app_name)
        return [asdict(s) for s in steps]

    def run(self, goal: str, app_name: str = "",
            max_retries: int = 1, task_id: Optional[str] = None) -> VisualTaskResult:
        """Plan and execute a visual task.

        Args:
            goal: Natural language task description
            app_name: Optional target app name
            max_retries: Max retry attempts on failure
            task_id: Optional task identifier

        Returns:
            VisualTaskResult with execution details
        """
        import uuid
        tid = task_id or f"visual_{uuid.uuid4().hex[:8]}"
        errors: List[str] = []

        try:
            # Phase 1: Observe current state
            observer = self._get_observer()
            initial_state = observer.observe()

            # Phase 2: Plan
            planner = self._get_planner()
            steps = planner.plan_for_goal(goal, app_name=app_name)
            plan_dicts = [asdict(s) for s in steps]

            # Phase 3: Execute
            executor = self._get_executor()
            results = executor.execute_plan(plan_dicts)

            executed = len([r for r in results if r.get("status") in ("success", "ok")])
            success = executed == len(plan_dicts)

            if not success:
                errors.append(f"{len(plan_dicts) - executed}/{len(plan_dicts)} steps failed")

            return VisualTaskResult(
                task_id=tid,
                goal=goal,
                plan_steps=len(steps),
                executed_steps=executed,
                success=success,
                errors=errors,
                details={
                    "app": app_name,
                    "initial_state": asdict(initial_state) if hasattr(initial_state, '__dataclass_fields__') else str(initial_state),
                    "step_results": results,
                },
            )
        except Exception as e:
            return VisualTaskResult(
                task_id=tid,
                goal=goal,
                plan_steps=0,
                executed_steps=0,
                success=False,
                errors=[str(e)],
                details={},
            )
