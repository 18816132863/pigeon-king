"""V49.0 Personal Knowledge Graph V5.

Lightweight local graph for semantic, episodic and procedural memory references.
Writes are guarded to avoid untrusted or low-confidence memory pollution.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Any

@dataclass
class MemoryNodeV5:
    node_id: str
    kind: str
    text: str
    confidence: float = 0.8
    source: str = "system"

@dataclass
class MemoryEdgeV5:
    source: str
    relation: str
    target: str

class PersonalKnowledgeGraphV5:
    def __init__(self, min_confidence: float = 0.65) -> None:
        self.min_confidence = min_confidence
        self.nodes: Dict[str, MemoryNodeV5] = {}
        self.edges: List[MemoryEdgeV5] = []
        self.rejected: List[Dict[str, Any]] = []

    def add_node(self, node: MemoryNodeV5) -> bool:
        if node.confidence < self.min_confidence or not node.text.strip():
            self.rejected.append({"node": asdict(node), "reason": "low_confidence_or_empty"})
            return False
        self.nodes[node.node_id] = node
        return True

    def add_edge(self, source: str, relation: str, target: str) -> bool:
        if source not in self.nodes or target not in self.nodes:
            self.rejected.append({"edge": {"source": source, "relation": relation, "target": target}, "reason": "missing_node"})
            return False
        self.edges.append(MemoryEdgeV5(source, relation, target))
        return True

    def export(self) -> Dict[str, Any]:
        return {
            "nodes": [asdict(n) for n in self.nodes.values()],
            "edges": [asdict(e) for e in self.edges],
            "rejected": self.rejected,
        }
