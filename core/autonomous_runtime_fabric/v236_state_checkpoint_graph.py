from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class StateCheckpointGraph:
    """V236: checkpoint DAG builder."""
    def build(self, checkpoints: list[str]) -> FabricArtifact:
        edges = [{"from": checkpoints[i-1], "to": checkpoints[i]} for i in range(1, len(checkpoints))]
        score = 0.9 if checkpoints else 0.4
        status = FabricStatus.READY if checkpoints else FabricStatus.WARN
        return FabricArtifact(new_id("ckgraph"), "state_checkpoint_graph", "checkpoint", status, score, {"nodes": checkpoints, "edges": edges})
