from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class DependencyGraphBuilder:
    """V213: dependency graph builder."""
    def build(self, modules: list[str]) -> ControlArtifact:
        edges = []
        for i, m in enumerate(modules):
            if i:
                edges.append({"from": modules[i-1], "to": m})
        return ControlArtifact(new_id("depgraph"), "dependency_graph", "dependency", PlaneStatus.READY, 0.9, {"nodes": modules, "edges": edges})
