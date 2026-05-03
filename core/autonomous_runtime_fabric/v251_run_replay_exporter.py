from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class RunReplayExporter:
    """V251: run replay export generator."""
    def export(self, run_id: str, steps: list[str]) -> FabricArtifact:
        replay = [{"idx": i, "step": step, "mode": "replay"} for i, step in enumerate(steps, 1)]
        return FabricArtifact(new_id("runreplay"), "run_replay_export", "replay_export", FabricStatus.READY, 0.9, {"run_id": run_id, "replay": replay})
