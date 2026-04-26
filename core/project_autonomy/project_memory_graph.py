class ProjectMemoryGraph:
    def build(self, project: dict, events: list[dict] | None = None) -> dict:
        events = events or []
        return {
            "status": "project_graph_ready",
            "project": project,
            "event_count": len(events),
            "nodes": [{"type": "project", "id": project.get("project_id", "project")}],
            "edges": [],
            "privacy": "local_only",
        }
