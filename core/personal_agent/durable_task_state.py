# -*- coding: utf-8 -*-
"""V86 durable task state store."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .schemas import TaskGraph, utc_now


class DurableTaskState:
    def __init__(self, root: str | Path = ".v86_state"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.graph_dir = self.root / "graphs"
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        self.event_log = self.root / "events.jsonl"

    def save_graph(self, graph: TaskGraph) -> Path:
        graph.updated_at = utc_now()
        path = self.graph_dir / f"{graph.graph_id}.json"
        path.write_text(json.dumps(graph.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        self.append_event(graph.graph_id, "graph_saved", {"nodes": len(graph.nodes)})
        return path

    def load_graph(self, graph_id: str) -> TaskGraph:
        path = self.graph_dir / f"{graph_id}.json"
        if not path.exists():
            raise KeyError(f"graph not found: {graph_id}")
        return TaskGraph.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def append_event(self, graph_id: str, event: str, detail: Dict[str, object] | None = None) -> None:
        payload = {"created_at": utc_now(), "graph_id": graph_id, "event": event, "detail": detail or {}}
        with self.event_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def list_graphs(self) -> List[str]:
        return sorted(p.stem for p in self.graph_dir.glob("*.json"))

    def latest_graph_id(self) -> Optional[str]:
        files = sorted(self.graph_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return files[0].stem if files else None
