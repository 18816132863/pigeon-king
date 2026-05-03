"""V29.2 Personal Memory Kernel V4.

L2 Memory Context:
- Semantic memory: durable facts.
- Episodic memory: task outcomes and failures.
- Procedural memory: preferred ways of doing.
- Preference memory: user's style, risk, interaction preferences.
- Guard prevents pollution, contradictions, and low-confidence writes.
- V29.1: Integrated KnowledgeGraphBridge for graph-backed semantic memory
  and PreferenceEvolutionBridge for long-term preference modeling.
- V29.2: Integrated Qdrant vector search, MultimodalSearcher, and
  CrossLingualSearcher into the query path.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib


@dataclass
class MemoryRecord:
    memory_id: str
    memory_type: str
    content: str
    confidence: float
    source: str
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "active"

    def to_dict(self):
        return asdict(self)


class MemoryWritebackGuardV4:
    forbidden_fragments = ["可能", "好像", "猜测", "不确定但记住", "临时"]

    def evaluate(self, memory_type: str, content: str, confidence: float, source: str) -> Dict[str, Any]:
        if not content.strip():
            return {"allow": False, "reason": "empty_content"}
        if confidence < 0.65:
            return {"allow": False, "reason": "low_confidence"}
        if any(f in content for f in self.forbidden_fragments) and memory_type in ("semantic", "profile"):
            return {"allow": False, "reason": "uncertain_semantic_memory"}
        if source not in ("user_confirmed", "task_verified", "system_observation", "procedure_success"):
            return {"allow": False, "reason": "untrusted_source"}
        return {"allow": True, "reason": "accepted"}


class PersonalMemoryKernelV4:
    def __init__(self, knowledge_graph_dir: str = ".knowledge_graph_state",
                 preference_evolution_dir: str = ".preference_evolution_state"):
        self.records: Dict[str, MemoryRecord] = {}
        self.guard = MemoryWritebackGuardV4()
        self._kg_dir = knowledge_graph_dir
        self._pref_dir = preference_evolution_dir
        self._kg_bridge = None
        self._pref_bridge = None
        self._qdrant_store = None
        self._multimodal_searcher = None
        self._cross_lingual_searcher = None

    def _kg(self):
        if self._kg_bridge is None:
            from memory_context.knowledge_graph_bridge import get_knowledge_graph_bridge
            self._kg_bridge = get_knowledge_graph_bridge(self._kg_dir)
        return self._kg_bridge

    def _pref(self):
        if self._pref_bridge is None:
            from memory_context.preference_evolution_bridge import get_preference_evolution_bridge
            self._pref_bridge = get_preference_evolution_bridge(self._pref_dir)
        return self._pref_bridge

    def _qdrant(self):
        """Lazy-init Qdrant memory store for semantic search."""
        if self._qdrant_store is None:
            from memory_context.vector.qdrant_store import QdrantMemoryStore
            self._qdrant_store = QdrantMemoryStore()
        return self._qdrant_store

    def _multimodal(self):
        """Lazy-init multimodal searcher."""
        if self._multimodal_searcher is None:
            from memory_context.multimodal.multimodal_search import MultimodalSearcher
            self._multimodal_searcher = MultimodalSearcher()
        return self._multimodal_searcher

    def _cross_lingual(self):
        """Lazy-init cross-lingual searcher."""
        if self._cross_lingual_searcher is None:
            from memory_context.cross_lingual.cross_lingual import CrossLingualSearcher
            self._cross_lingual_searcher = CrossLingualSearcher()
        return self._cross_lingual_searcher

    def write(self, memory_type: str, content: str, *, confidence: float, source: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        decision = self.guard.evaluate(memory_type, content, confidence, source)
        if not decision["allow"]:
            return {"status": "rejected", **decision}
        memory_id = self._make_id(memory_type, content)
        if memory_id in self.records:
            return {"status": "deduped", "memory_id": memory_id}
        record = MemoryRecord(memory_id, memory_type, content, confidence, source, tags or [])
        self.records[memory_id] = record

        # ── V29.1: Side-effect to Knowledge Graph ──
        kg_node_id = None
        try:
            kg_node_id = self._kg().on_memory_written(
                memory_type, content,
                confidence=confidence,
                source=source,
                tags=tags,
            )
        except Exception:
            pass  # KG is best-effort, don't block memory write

        # ── V29.1: Side-effect to Preference Evolution ──
        pref_result = None
        if memory_type == "preference":
            try:
                pref_result = self._pref().ingest_from_interaction(
                    interaction_key=f"memory_{memory_id}",
                    value={"content": content[:200], "confidence": confidence},
                    confidence_delta=0.08,
                )
            except Exception:
                pass

        # ── V29.2: Side-effect to Qdrant vector store ──
        qdrant_id = None
        try:
            qdrant_id = self._qdrant().add(
                content,
                metadata={
                    "type": memory_type,
                    "confidence": confidence,
                    "source": source,
                    "tags": ",".join(tags or []),
                },
            )
        except Exception:
            pass

        result = {
            "status": "written",
            "memory_id": memory_id,
            "record": record.to_dict(),
        }
        if kg_node_id:
            result["kg_node_id"] = kg_node_id
        if pref_result:
            result["preference_status"] = pref_result.get("status")
        if qdrant_id:
            result["vector_id"] = qdrant_id

        return result

    def query(self, memory_type: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        items = list(self.records.values())
        if memory_type:
            items = [r for r in items if r.memory_type == memory_type]
        if tags:
            want = set(tags)
            items = [r for r in items if want.intersection(r.tags)]
        return [r.to_dict() for r in items if r.status == "active"]

    # ── V29.2: Semantic / Multi-modal / Cross-lingual search ─────

    def search_semantic(self, query: str, limit: int = 5, score_threshold: float = 0.5,
                        filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """语义搜索记忆（通过 Qdrant 向量检索）。

        Args:
            query: 自然语言查询
            limit: 返回条数
            score_threshold: 最低相似度
            filter_type: 按记忆类型过滤（semantic/episodic/procedural/preference）

        Returns:
            [{"id", "score", "text", "type", "source", "confidence", "timestamp"}, ...]
        """
        filter_by = {"type": filter_type} if filter_type else None
        try:
            return self._qdrant().search(query, limit=limit, score_threshold=score_threshold, filter_by=filter_by)
        except Exception as e:
            # Fallback to in-memory keyword match
            return self._fallback_keyword_search(query, limit, filter_type)

    def search_multimodal(self, text: Optional[str] = None,
                          image_path: Optional[str] = None,
                          limit: int = 5) -> List[Dict[str, Any]]:
        """多模态搜索。

        支持纯文本、纯图像、或文本+图像联合搜索。
        当前覆用到 Qdrant 向量搜索 + MultimodalSearcher 编码。
        """
        searcher = self._multimodal()
        results = []
        if text:
            # Use Qdrant semantic search for text
            results = self._qdrant().search(text, limit=limit, score_threshold=0.4)
        if image_path:
            # Use multimodal encoder for image
            searcher.add_image(image_path, {"source": "multimodal_query"})
            img_vec = searcher.encoder.encode_image(image_path)
            img_results = self._qdrant().search(
                query="", query_vector=list(img_vec), limit=limit, score_threshold=0.3
            )
            results.extend(img_results)
        return results[:limit]

    def search_cross_lingual(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """跨语言搜索。

        自动检测查询语言，在中文记忆中跨语言检索。
        """
        searcher = self._cross_lingual()
        lang = searcher.detector.detect(query)
        # Cross-lingual: use the same semantic path since Qdrant embeddings are multilingual
        results = self._qdrant().search(query, limit=limit, score_threshold=0.45)
        return {
            "query_language": lang,
            "results": results,
            "method": "semantic_cross_lingual",
        }

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """统一回忆接口：先精搜（keyword），再语义搜，合并去重。"""
        keyword_hits = self.query()
        matched = []
        query_lower = query.lower()
        for r in keyword_hits:
            if query_lower in r["content"].lower():
                matched.append({**r, "score": 0.9, "method": "keyword"})
        if len(matched) >= limit:
            return matched[:limit]

        try:
            semantic = self._qdrant().search(query, limit=limit, score_threshold=0.5)
            seen_ids = {m.get("memory_id", "") for m in matched}
            for s in semantic:
                if s.get("text", "")[:16] not in seen_ids:
                    matched.append({**s, "method": "semantic"})
        except Exception:
            pass

        return matched[:limit]

    def stats(self) -> Dict[str, Any]:
        """返回内核统计信息（含向量存储）。"""
        qdrant_info = {}
        try:
            qdrant_info = self._qdrant().stats()
        except Exception:
            qdrant_info = {"status": "unavailable"}

        kg_info = {}
        try:
            kg = self._kg()
            kg_info = {
                "nodes": len(kg.graph.nodes),
                "edges": len(kg.graph.edges) if hasattr(kg.graph, 'edges') else sum(len(e) for e in kg.graph.edges.values()) if hasattr(kg.graph, 'edges') else "N/A",
                "snapshots": len(kg.snapshots),
            }
        except Exception:
            kg_info = {"status": "unavailable"}

        pref_info = {}
        try:
            pref = self._pref()
            signals = getattr(pref.model, '_signals', getattr(pref.model, 'signals', []))
            pref_info = {
                "signal_count": len(signals) if isinstance(signals, (list, dict)) else "N/A",
                "snapshots": len(pref.snapshots),
            }
        except Exception:
            pref_info = {"status": "unavailable"}

        return {
            "in_memory_records": len(self.records),
            "vector_store": qdrant_info,
            "knowledge_graph": kg_info,
            "preference_evolution": pref_info,
        }

    def _fallback_keyword_search(self, query: str, limit: int = 5, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Qdrant 不可用时的关键词回退搜索。"""
        results = []
        query_lower = query.lower()
        items = list(self.records.values())
        if filter_type:
            items = [r for r in items if r.memory_type == filter_type]
        for r in items:
            if r.status != "active":
                continue
            score = 0.0
            if query_lower in r.content.lower():
                score = 0.7
            elif any(w in r.content.lower() for w in query_lower.split()):
                score = 0.4
            if score > 0:
                results.append({
                    "id": r.memory_id,
                    "score": score,
                    "text": r.content,
                    "type": r.memory_type,
                    "source": r.source,
                    "confidence": r.confidence,
                    "timestamp": r.created_at,
                    "method": "fallback_keyword",
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _make_id(self, memory_type: str, content: str) -> str:
        return "mem_" + hashlib.sha256(f"{memory_type}:{content}".encode("utf-8")).hexdigest()[:16]
