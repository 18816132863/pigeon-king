from __future__ import annotations

from .milestone_planner import MilestonePlanner
from .project_memory_graph import ProjectMemoryGraph
from .autonomous_project_review import AutonomousProjectReview


class ProjectBrain:
    """Long-horizon project autonomy for multi-day/multi-version goals."""

    def __init__(self) -> None:
        self.planner = MilestonePlanner()
        self.graph = ProjectMemoryGraph()
        self.review = AutonomousProjectReview()

    def start_project(self, project_goal: str, events: list[dict] | None = None) -> dict:
        project = {"project_id": f"project_{abs(hash(project_goal))}", "goal": project_goal, "status": "active"}
        milestones = self.planner.plan(project_goal)
        graph = self.graph.build(project, events)
        review = self.review.review(project, milestones)
        return {
            "status": "project_autonomy_ready",
            "project": project,
            "milestones": milestones,
            "memory_graph": graph,
            "review": review,
        }
