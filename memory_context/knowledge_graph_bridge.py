"""
V10.1 Knowledge Graph Bridge

Bridges PersonalKnowledgeGraphV5 into the live memory pipeline.
- Every accepted memory write → graph node
- Relationship memory writes → graph edges
- Exports periodic snapshots for downstream consumers
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

from memory_context.personal_knowledge_graph_v5 import (
    PersonalKnowledgeGraphV5,
    MemoryNodeV5,
    MemoryEdgeV5,
)


@dataclass
class GraphSnapshotMeta:
    snapshot_id: str
    created_at: str
    node_count: int
    edge_count: int
    rejected_count: int


class KnowledgeGraphBridge:
    """Bridge that wraps PersonalKnowledgeGraphV5 into the memory pipeline."""

    def __init__(self, storage_dir: str | Path = ".knowledge_graph_state"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.graph = PersonalKnowledgeGraphV5(min_confidence=0.60)
        self.snapshots: List[GraphSnapshotMeta] = []
        self._load_latest()

    # ── Write hooks ────────────────────────────────────────────

    def on_memory_written(self, memory_type: str, content: str, *,
                          confidence: float = 0.8,
                          source: str = "system",
                          tags: Optional[List[str]] = None) -> Optional[str]:
        """Called after a memory record is accepted by the memory kernel."""
        node_kind = self._map_memory_type(memory_type)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        node_id = f"{node_kind}_{ts}_{abs(hash(content)) % 100000}"

        node = MemoryNodeV5(
            node_id=node_id,
            kind=node_kind,
            text=content[:500],
            confidence=float(confidence),
            source=source,
        )
        if not self.graph.add_node(node):
            return None

        # Add implicit edges for tagged relationships
        if tags:
            for tag in tags:
                if isinstance(tag, str) and tag.startswith("rel:"):
                    relation = tag[4:]
                    # Find potential target nodes
                    for existing_id in list(self.graph.nodes.keys()):
                        if existing_id != node_id:
                            self.graph.add_edge(
                                node_id, relation, existing_id
                            )

        return node_id

    def on_relationship_written(self, source_content: str,
                                 relation: str,
                                 target_content: str,
                                 confidence: float = 0.7) -> bool:
        """Create a relationship edge between two memory nodes."""
        source_id = f"entity_{abs(hash(source_content)) % 100000}"
        target_id = f"entity_{abs(hash(target_content)) % 100000}"

        # Ensure both nodes exist (create lightweight ones if needed)
        if source_id not in self.graph.nodes:
            self.graph.add_node(MemoryNodeV5(
                node_id=source_id,
                kind="entity",
                text=source_content[:200],
                confidence=confidence,
            ))
        if target_id not in self.graph.nodes:
            self.graph.add_node(MemoryNodeV5(
                node_id=target_id,
                kind="entity",
                text=target_content[:200],
                confidence=confidence,
            ))

        return self.graph.add_edge(source_id, relation, target_id)

    # ── Read / query ───────────────────────────────────────────

    def query_related(self, content: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Find nodes and edges related to a given content."""
        node_id = f"entity_{abs(hash(content)) % 100000}"
        related: List[Dict[str, Any]] = []

        if node_id in self.graph.nodes:
            # 1-hop edges
            for edge in self.graph.edges:
                if edge.source == node_id or edge.target == node_id:
                    other = edge.target if edge.source == node_id else edge.source
                    if other in self.graph.nodes:
                        related.append({
                            "node": asdict(self.graph.nodes[other]),
                            "relation": edge.relation,
                            "direction": "outgoing" if edge.source == node_id else "incoming",
                            "depth": 1,
                        })

        return sorted(related, key=lambda r: r["depth"])

    def export(self) -> Dict[str, Any]:
        """Full graph export for downstream consumers."""
        return self.graph.export()

    def export_nodes_by_kind(self, kind: str) -> List[Dict[str, Any]]:
        """Export all nodes of a specific kind."""
        return [
            asdict(n) for n in self.graph.nodes.values() if n.kind == kind
        ]

    # ── Persistence ────────────────────────────────────────────

    def snapshot(self) -> GraphSnapshotMeta:
        """Persist current graph to disk."""
        ts = datetime.now(timezone.utc)
        meta = GraphSnapshotMeta(
            snapshot_id=ts.strftime("%Y%m%d_%H%M%S"),
            created_at=ts.isoformat(),
            node_count=len(self.graph.nodes),
            edge_count=len(self.graph.edges),
            rejected_count=len(self.graph.rejected),
        )

        path = self.storage_dir / f"kg_snapshot_{meta.snapshot_id}.json"
        path.write_text(json.dumps(self.export(), ensure_ascii=False, indent=2))

        self.snapshots.append(meta)
        # Keep last 10 snapshots
        if len(self.snapshots) > 10:
            oldest = self.snapshots.pop(0)
            old_path = self.storage_dir / f"kg_snapshot_{oldest.snapshot_id}.json"
            if old_path.exists():
                old_path.unlink()

        return meta

    def _load_latest(self):
        """Restore latest snapshot on init."""
        snapshots = sorted(self.storage_dir.glob("kg_snapshot_*.json"), reverse=True)
        if not snapshots:
            return
        try:
            data = json.loads(snapshots[0].read_text())
            for nd in data.get("nodes", []):
                node = MemoryNodeV5(**nd)
                self.graph.nodes[node.node_id] = node
            for ed in data.get("edges", []):
                self.graph.edges.append(MemoryEdgeV5(**ed))
            self.graph.rejected = data.get("rejected", [])
        except Exception:
            pass  # Best-effort restore

    # ── Helpers ────────────────────────────────────────────────

    @staticmethod
    def _map_memory_type(memory_type: str) -> str:
        mapping = {
            "semantic": "knowledge",
            "episodic": "event",
            "procedural": "skill",
            "preference": "preference",
        }
        return mapping.get(memory_type, "misc")

    @property
    def stats(self) -> Dict[str, int]:
        return {
            "nodes": len(self.graph.nodes),
            "edges": len(self.graph.edges),
            "rejected": len(self.graph.rejected),
            "snapshots": len(self.snapshots),
        }


# Singleton
_GRAPH_BRIDGE: Optional[KnowledgeGraphBridge] = None


def get_knowledge_graph_bridge(storage_dir: str = ".knowledge_graph_state") -> KnowledgeGraphBridge:
    global _GRAPH_BRIDGE
    if _GRAPH_BRIDGE is None:
        _GRAPH_BRIDGE = KnowledgeGraphBridge(storage_dir)
    return _GRAPH_BRIDGE
