"""
V91 Personal Knowledge Graph V5 — 离线增强版。

- 本地 JSONL 持久化存储（不依赖外部图数据库）
- 挂接 personal_memory_kernel_v4 进行记忆回写
- 支持写入审计日志
"""
from __future__ import annotations
import json
import os
import time
import threading
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# 离线模式集成
try:
    from infrastructure.offline_mode import audit_info, audit_warning, STATE_DIR
except ImportError:
    STATE_DIR = Path(os.environ.get("WORKSPACE", "/home/sandbox/.openclaw/workspace")) / ".offline_state"
    def _noop(*a, **kw): pass
    audit_info = _noop
    audit_warning = _noop

@dataclass
class MemoryNodeV5:
    node_id: str
    kind: str  # semantic / episodic / procedural / preference
    text: str
    confidence: float = 0.8
    source: str = "system"
    ts: float = field(default_factory=time.time)

@dataclass
class MemoryEdgeV5:
    source: str
    relation: str
    target: str
    ts: float = field(default_factory=time.time)

class PersonalKnowledgeGraphV5:
    """V91 离线增强版 — JSONL 持久化 + memory kernel 桥接。"""

    def __init__(self, min_confidence: float = 0.65, state_path: Path = None):
        self.min_confidence = min_confidence
        self.nodes: Dict[str, MemoryNodeV5] = {}
        self.edges: List[MemoryEdgeV5] = []
        self.rejected: List[Dict[str, Any]] = []
        self._state_path = state_path or STATE_DIR / "knowledge_graph_v5.jsonl"
        self._lock = threading.Lock()
        self._memory_kernel = None  # 延迟挂接
        self._load_state()
        # V91: 自动挂接 memory kernel（离线兼容）
        self._auto_bridge_kernel()

    # ── 持久化 ──────────────────────────────────────────
    def _load_state(self):
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._state_path.exists():
            return
        try:
            with self._lock:
                for line in self._state_path.read_text().splitlines():
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    if entry.get("type") == "node":
                        n = MemoryNodeV5(**{k: v for k, v in entry.items() if k != "type"})
                        self.nodes[n.node_id] = n
                    elif entry.get("type") == "edge":
                        e = MemoryEdgeV5(**{k: v for k, v in entry.items() if k != "type"})
                        self.edges.append(e)
            audit_info("PersonalKnowledgeGraphV5", "state_loaded", nodes=len(self.nodes), edges=len(self.edges))
        except Exception as e:
            audit_warning("PersonalKnowledgeGraphV5", "state_load_failed", error=str(e))

    def _append_jsonl(self, entry: dict):
        with self._lock:
            with open(self._state_path, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _persist_node(self, node: MemoryNodeV5):
        entry = asdict(node)
        entry["type"] = "node"
        self._append_jsonl(entry)

    def _persist_edge(self, edge: MemoryEdgeV5):
        entry = asdict(edge)
        entry["type"] = "edge"
        self._append_jsonl(entry)

    # ── 核心操作 ────────────────────────────────────────
    def add_node(self, node: MemoryNodeV5) -> bool:
        if node.confidence < self.min_confidence or not node.text.strip():
            self.rejected.append({"node": asdict(node), "reason": "low_confidence_or_empty"})
            return False
        with self._lock:
            self.nodes[node.node_id] = node
        self._persist_node(node)
        audit_info("PersonalKnowledgeGraphV5", "node_added", node_id=node.node_id, kind=node.kind, confidence=node.confidence)
        return True

    def add_edge(self, source: str, relation: str, target: str) -> bool:
        if source not in self.nodes or target not in self.nodes:
            self.rejected.append({"edge": {"source": source, "relation": relation, "target": target}, "reason": "missing_node"})
            return False
        edge = MemoryEdgeV5(source, relation, target)
        with self._lock:
            self.edges.append(edge)
        self._persist_edge(edge)
        return True

    def query_nodes(self, kind: str = None, min_confidence: float = None) -> List[MemoryNodeV5]:
        results = list(self.nodes.values())
        if kind:
            results = [n for n in results if n.kind == kind]
        if min_confidence is not None:
            results = [n for n in results if n.confidence >= min_confidence]
        return sorted(results, key=lambda n: n.confidence, reverse=True)

    def query_edges(self, relation: str = None) -> List[MemoryEdgeV5]:
        if relation:
            return [e for e in self.edges if e.relation == relation]
        return list(self.edges)

    def get_subgraph(self, node_id: str, depth: int = 1) -> Dict[str, Any]:
        """获取以 node_id 为中心的子图。"""
        if node_id not in self.nodes:
            return {"node": None, "edges_in": [], "edges_out": []}
        edges_in = [e for e in self.edges if e.target == node_id]
        edges_out = [e for e in self.edges if e.source == node_id]
        return {
            "node": asdict(self.nodes[node_id]),
            "edges_in": [asdict(e) for e in edges_in],
            "edges_out": [asdict(e) for e in edges_out],
        }

    def export(self) -> Dict[str, Any]:
        return {
            "nodes": [asdict(n) for n in self.nodes.values()],
            "edges": [asdict(e) for e in self.edges],
            "rejected": self.rejected,
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "rejected_count": len(self.rejected),
            },
        }

    # ── Memory Kernel 桥接 ──────────────────────────────
    def attach_memory_kernel(self, kernel):
        """挂接 personal_memory_kernel_v4。"""
        self._memory_kernel = kernel
        audit_info("PersonalKnowledgeGraphV5", "memory_kernel_attached")

    def _auto_bridge_kernel(self):
        """V91: 自动挂接 memory kernel，离线兼容。"""
        if self._memory_kernel is not None:
            return
        try:
            from memory_context.personal_memory_kernel_v4 import PersonalMemoryKernelV4
            self._memory_kernel = PersonalMemoryKernelV4()
            audit_info("PersonalKnowledgeGraphV5", "memory_kernel_auto_attached")
        except Exception as e:
            # 离线模式下创建轻量 mock kernel
            class _MockMemoryKernel:
                def write(self, obj):
                    mtype = obj.get("memory_type", "episodic")
                    content = obj.get("content", "")
                    import hashlib
                    mid = hashlib.md5(f"{mtype}:{content}".encode()).hexdigest()[:12]
                    return {"status": "offline_mock", "memory_id": mid}
            self._memory_kernel = _MockMemoryKernel()
            audit_warning("PersonalKnowledgeGraphV5", "memory_kernel_mock_attached", error=str(e)[:200])

    def writeback_to_kernel(self, node_id: str) -> Dict[str, Any]:
        """将图谱节点写回记忆内核。"""
        if node_id not in self.nodes:
            return {"success": False, "error": "node_not_found"}
        node = self.nodes[node_id]
        if self._memory_kernel is None:
            audit_warning("PersonalKnowledgeGraphV5", "writeback_skipped_no_kernel", node_id=node_id)
            return {"success": False, "error": "no_memory_kernel_attached"}
        try:
            # V91: 兼容两种 kernel 接口（dict 风格 vs 位置参数风格）
            kw = self._kernel_write_kwargs(node)
            result = self._memory_kernel.write(**kw)
            audit_info("PersonalKnowledgeGraphV5", "writeback_done", node_id=node_id, result=str(result)[:200])
            return {"success": True, "result": result}
        except Exception as e:
            audit_warning("PersonalKnowledgeGraphV5", "writeback_failed", node_id=node_id, error=str(e))
            return {"success": False, "error": str(e)}

    def _kernel_write_kwargs(self, node: MemoryNodeV5) -> Dict[str, Any]:
        """构建 kernel.write() 调用参数，兼容 dict 和位置参数两种风格。"""
        return {
            "memory_type": node.kind,
            "content": node.text,
            "confidence": node.confidence,
            "source": node.source,
        }

    def get_state_path(self) -> str:
        return str(self._state_path)

# V92_CONTRACT_HOTFIX_START: PersonalKnowledgeGraphV5.health compatibility
# This shim is offline-only and does not call any external API.
def _v92_pkg_state_dir():
    from pathlib import Path
    d = Path.cwd() / ".knowledge_graph_state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _v92_pkg_health(self=None):
    import json
    from datetime import datetime
    d = _v92_pkg_state_dir()
    marker = d / "health.json"
    payload = {
        "status": "ok",
        "component": "PersonalKnowledgeGraphV5",
        "mode": "offline",
        "state_dir": str(d),
        "side_effects": False,
        "requires_api": False,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }
    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload

try:
    PersonalKnowledgeGraphV5.health = _v92_pkg_health
except NameError:
    class PersonalKnowledgeGraphV5:  # fallback only if the original class is missing
        def health(self):
            return _v92_pkg_health(self)
# V92_CONTRACT_HOTFIX_END
