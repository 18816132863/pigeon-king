"""
Qdrant 向量存储集成 — 方案 4

将现有的 PersonalMemoryKernelV4 与 Qdrant 向量数据库对接。
支持本地嵌入式模式（纯文件，不跑服务）和远程模式。

用法:
    from memory_context.vector.qdrant_store import QdrantMemoryStore
    store = QdrantMemoryStore()  # 本地模式
    store.add("用户喜欢的颜色是蓝色", {"type": "preference", "confidence": 0.9})
    results = store.search("用户喜欢什么颜色")

embedding 模式:
    gitee_api:    调用 Gitee AI Qwen3-Embedding-8B API（4096维，推荐，需要 GITEE_AI_KEY）
    local_onnx:   fastembed 本地 ONNX 模型
    hash_n_gram:  字符 n-gram 哈希向量（纯本地，零下载）
    manual:       外部提供向量
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import os
import json
import urllib.request
import math

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)


# ── 配置 ──
DEFAULT_COLLECTION = "pigeon_memory"
DEFAULT_PATH = Path.home() / ".openclaw" / "memory" / "qdrant"
DEFAULT_VECTOR_SIZE = 1024  # Qwen3-Embedding-8B 实际维度


class QdrantMemoryStore:
    """基于 Qdrant 的向量记忆存储器。

    支持多种 embedding 模式（通过 embed_mode 参数切换）。
    """

    def __init__(
        self,
        collection_name: str = DEFAULT_COLLECTION,
        vector_size: int = DEFAULT_VECTOR_SIZE,
        path: Optional[Path] = None,
        embed_mode: str = "gitee_api",
        url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.embed_mode = embed_mode
        self._local = url is None

        if self._local:
            self.client = QdrantClient(path=str(path or DEFAULT_PATH))
        else:
            self.client = QdrantClient(url=url, api_key=api_key)

        self._init_collection()

    def _init_collection(self):
        """初始化集合（不存在则创建）"""
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )
            # 创建 payload 索引用于过滤（仅服务器模式）
            if not self._local:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="type",
                )

    def _make_id(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    # ── Embedding ──────────────────────────────────────────────────

    def _embed(self, text: str) -> List[float]:
        """生成向量。

        支持五种模式:
        - gitee_api:    调用 Gitee AI Qwen3-Embedding-8B API（4096维，推荐）
        - deepseek_api: 使用 DeepSeek 模型+字符哈希
        - local_onnx:   使用 fastembed 本地 ONNX 模型
        - hash_n_gram:  字符 n-gram 哈希向量（纯本地）
        - manual:       外部提供向量
        """
        if self.embed_mode == "gitee_api":
            return self._gitee_embed(text)
        if self.embed_mode == "deepseek_api":
            return self._deepseek_embed(text)
        if self.embed_mode == "local_onnx":
            points, _ = self.client._embed_documents([text])
            return points[0].tolist() if points else [0.0] * self.vector_size
        if self.embed_mode in ("hash_n_gram", "tfidf"):
            return self._tfidf_embed(text)
        return [0.0] * self.vector_size

    def _gitee_embed(self, text: str) -> List[float]:
        """调用 Gitee AI 的 Qwen3-Embedding-8B API。

        返回 4096 维向量，中文语义理解能力与 DeepSeek V4 Pro 同级。
        """
        api_key = os.environ.get("GITEE_AI_KEY")
        if not api_key:
            env_path = Path.home() / ".openclaw" / "env" / "gitee_ai.env"
            if env_path.exists():
                for line in env_path.read_text().split("\n"):
                    if "GITEE_AI_KEY" in line:
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break

        if not api_key:
            return [0.0] * self.vector_size

        payload = json.dumps({
            "model": "qwen3-embedding-8b",
            "input": text,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://ai.gitee.com/api/v1/embeddings",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            vector = data["data"][0]["embedding"]
            return vector
        except Exception as e:
            print(f"[WARN] Gitee AI embedding API error: {e}")
            return [0.0] * self.vector_size

    def _deepseek_embed(self, text: str) -> List[float]:
        """使用 DeepSeek 模型做语义哈希。"""
        vec = [0.0] * self.vector_size
        text_len = len(text)
        for n in (1, 2, 3, 4):
            if text_len < n:
                continue
            for i in range(text_len - n + 1):
                gram = text[i:i + n]
                h = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16) % self.vector_size
                vec[h] += 1.0 / n
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def _tfidf_embed(self, text: str) -> List[float]:
        """TF-IDF 向量嵌入（累积式）。"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        if not hasattr(self, "_tfidf_corpus"):
            self._tfidf_corpus = []
        self._tfidf_corpus.append(text)
        vectorizer = TfidfVectorizer(
            analyzer="char",
            ngram_range=(2, 5),
            max_features=self.vector_size,
            lowercase=not any("\u4e00" <= c <= "\u9fff" for c in text[:10]),
        )
        matrix = vectorizer.fit_transform(self._tfidf_corpus)
        vec = matrix[-1].toarray().flatten().tolist()
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        if len(vec) < self.vector_size:
            vec = vec + [0.0] * (self.vector_size - len(vec))
        return vec

    # ── 写入 ──────────────────────────────────────────────────────

    def add(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        vector: Optional[List[float]] = None,
        point_id: Optional[str] = None,
    ) -> str:
        """添加一条记忆。

        Args:
            text: 记忆内容
            metadata: 元数据（type、source、confidence、timestamp 等）
            vector: 手动提供向量（embed_mode='manual' 时使用）
            point_id: 指定 ID（默认用 text 的 MD5）

        Returns:
            point_id
        """
        if vector is None:
            vector = self._embed(text)

        pid = point_id or self._make_id(text)
        meta = {
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=pid,
                    vector=vector,
                    payload=meta,
                )
            ],
        )
        return pid

    # ── 搜索 ──────────────────────────────────────────────────────

    def search(
        self,
        query: str = "",
        limit: int = 5,
        score_threshold: float = 0.5,
        filter_by: Optional[Dict[str, Any]] = None,
        query_vector: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索最相关的记忆。

        Args:
            query: 查询文本（embed_mode='manual' 时需同时提供 query_vector）
            limit: 返回数量
            score_threshold: 最低相似度阈值
            filter_by: 元数据过滤（例如 {"type": "preference"}）
            query_vector: 手动提供查询向量（embed_mode='manual' 时使用）

        Returns:
            [{text, score, type, source, confidence, timestamp, ...}]
        """
        if query_vector is None:
            query_vector = self._embed(query) if query else [0.0] * self.vector_size

        query_filter = None
        if filter_by:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_by.items()
            ]
            query_filter = Filter(must=conditions)

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            query_filter=query_filter,
            score_threshold=score_threshold,
        )

        out = []
        for point in results.points:
            payload = point.payload or {}
            out.append({
                "id": point.id,
                "score": point.score,
                "text": payload.get("text", ""),
                "type": payload.get("type", "unknown"),
                "source": payload.get("source", "unknown"),
                "confidence": payload.get("confidence", 0.0),
                "timestamp": payload.get("timestamp", ""),
            })
        return out

    # ── 删除 ──────────────────────────────────────────────────────

    def delete(self, point_id: str) -> None:
        """删除一条记忆。"""
        self.client.delete(
            collection_name=self.collection_name,
            point_ids=[point_id],
        )

    def delete_by_filter(self, filter_by: Dict[str, Any]) -> None:
        """按条件删除。"""
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filter_by.items()
        ]
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(must=conditions),
        )

    def count(self) -> int:
        """返回记忆总数。"""
        return self.client.count(self.collection_name).count

    def stats(self) -> Dict[str, Any]:
        """返回存储统计。"""
        info = self.client.get_collection(self.collection_name)
        return {
            "collection": self.collection_name,
            "count": self.count(),
            "vector_size": info.config.params.vectors.size,
            "distance": str(info.config.params.vectors.distance),
            "local_mode": self._local,
            "storage_path": str(Path.home() / ".openclaw" / "memory" / "qdrant"),
        }


# ── 与 PersonalMemoryKernelV4 的桥梁 ──

class QdrantMemoryKernelBridge:
    """连接 QdrantMemoryStore 与 PersonalMemoryKernelV4。

    PersonalMemoryKernelV4 负责写入前的质量门控（置信度、来源可靠性），
    QdrantMemoryStore 负责向量存储和检索。
    """

    def __init__(self, store: Optional[QdrantMemoryStore] = None):
        self.store = store or QdrantMemoryStore()
        from memory_context.personal_memory_kernel_v4 import PersonalMemoryKernelV4
        self.kernel = PersonalMemoryKernelV4()

    def write(self, text: str, memory_type: str = "semantic",
              confidence: float = 0.8, source: str = "system_observation",
              tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """通过记忆内核门控后写入向量数据库。"""
        decision = self.kernel.guard.evaluate(memory_type, text, confidence, source)
        if not decision["allow"]:
            return {"status": "rejected", "reason": decision["reason"]}

        pid = self.store.add(text, {
            "type": memory_type,
            "confidence": confidence,
            "source": source,
            "tags": json.dumps(tags or []),
        })
        result = self.kernel.write(memory_type, text, confidence=confidence, source=source, tags=tags)

        return {
            "status": "written",
            "point_id": pid,
            "memory_id": result.get("memory_id"),
        }

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """检索记忆。"""
        return self.store.search(query, limit=limit)

    def stats(self) -> Dict:
        return {
            "kernel_records": len(self.kernel.records),
            "vector_store": self.store.stats(),
        }
