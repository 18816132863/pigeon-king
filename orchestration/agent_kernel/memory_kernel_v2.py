# agent_kernel/memory_kernel_v2.py
# V25.3 — 向量记忆内核
# 在原有 SQLite 关键词搜索之上，添加语义向量检索
# 无外部依赖，纯 Python 实现 n-gram 向量 + 余弦相似度

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import sqlite3

VALID_TYPES = {"semantic", "episodic", "procedural", "profile", "preference"}


@dataclass
class MemoryRecord:
    memory_id: str
    memory_type: str
    content: str
    tags: list
    confidence: float = 0.7
    source: str = "agent_kernel"
    status: str = "active"
    created_at: str = ""

    def __post_init__(self):
        if self.memory_type not in VALID_TYPES:
            raise ValueError(f"invalid memory_type: {self.memory_type}")
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------------
# n-gram 向量化（纯 Python，无外部依赖）
# ------------------------------------------------------------------


def _tokenize(text: str) -> List[str]:
    """分词：小写 + 拆分驼峰 + 去标点"""
    text = text.lower()
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)  # 驼峰拆分
    tokens = re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text)  # 中英数字
    return tokens


def _ngrams(tokens: List[str], n: int = 2) -> List[str]:
    """生成 n-gram"""
    return ["_".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def embedding_vector(
    text: str,
    max_features: int = 256,
) -> Dict[str, float]:
    """将文本转为稀疏向量（中文单字 + 混合 n-gram → TF 权重）

    对于中文短文本效果更好：
    - 1-gram（中文字符）
    - 2-gram（双字）
    - unigram（英文字词）
    """
    tokens = _tokenize(text)
    if not tokens:
        return {}

    # 中文字符 / 英文 / 数字
    chars: List[str] = []
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            chars.append(ch)

    bigrams: List[str] = (
        [chars[i] + chars[i + 1] for i in range(len(chars) - 1)]
        if len(chars) >= 2
        else []
    )

    # 特征组合：中文字 + 中文双字 + 英文词 + 英文双词
    features: List[str] = chars + bigrams + tokens

    if len(tokens) >= 2:
        features += [
            tokens[i] + "_" + tokens[i + 1] for i in range(len(tokens) - 1)
        ]

    if not features:
        return {}

    count = Counter(features)
    total = sum(count.values())
    vec = {}
    for gram, cnt in count.most_common(max_features):
        vec[gram] = cnt / total
    return vec


def cosine_similarity(
    vec_a: Dict[str, float],
    vec_b: Dict[str, float],
) -> float:
    """余弦相似度"""
    if not vec_a or not vec_b:
        return 0.0
    keys = set(vec_a) & set(vec_b)
    if not keys:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in keys)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_search_score(query: str, content: str) -> float:
    """语义搜索分数（关键词匹配 + 向量相似度混合）"""
    q_tokens = set(_tokenize(query))
    c_tokens = set(_tokenize(content))

    # 关键词重叠率
    overlap = q_tokens & c_tokens
    keyword_score = len(overlap) / max(len(q_tokens), 1)

    # n-gram 向量相似度
    q_vec = embedding_vector(query)
    c_vec = embedding_vector(content)
    vec_score = cosine_similarity(q_vec, c_vec)

    # 混合得分（关键词 0.5 + 向量 0.5）
    return keyword_score * 0.5 + vec_score * 0.5


# ------------------------------------------------------------------
# 向量记忆内核
# ------------------------------------------------------------------


class VectorMemoryKernel:
    """向量记忆内核

    兼容 PersonalMemoryKernel 接口，并在其基础上增加语义检索。
    支持混合搜索（关键词 + 向量相似度）。
    """

    def __init__(self, db: str = ":memory:"):
        self.conn = sqlite3.connect(str(db))
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS memories(
                id TEXT PRIMARY KEY,
                type TEXT,
                content TEXT,
                tags TEXT,
                confidence REAL,
                source TEXT,
                status TEXT,
                created_at TEXT,
                embedding TEXT
            )"""
        )
        self.conn.commit()

    def add(self, record: MemoryRecord, compute_embedding: bool = True) -> str:
        """添加记忆记录

        Args:
            record: 记忆记录
            compute_embedding: 是否计算并存储向量

        Returns:
            记忆 ID
        """
        embedding = None
        if compute_embedding and record.content:
            vec = embedding_vector(record.content)
            embedding = json.dumps(vec, ensure_ascii=False)

        self.conn.execute(
            "INSERT OR REPLACE INTO memories VALUES(?,?,?,?,?,?,?,?,?)",
            (
                record.memory_id,
                record.memory_type,
                record.content,
                json.dumps(record.tags, ensure_ascii=False),
                record.confidence,
                record.source,
                record.status,
                record.created_at,
                embedding,
            ),
        )
        self.conn.commit()
        return record.memory_id

    def search(
        self,
        query: str = "",
        memory_type: Optional[str] = None,
        min_confidence: float = 0,
        limit: int = 20,
        mode: str = "hybrid",
    ) -> List[Dict[str, Any]]:
        """搜索记忆

        支持三种模式:
        - "keyword": 传统关键词搜索（向后兼容 PersonalMemoryKernel）
        - "semantic": 纯语义向量搜索
        - "hybrid":  关键词 + 向量混合搜索（默认）

        Args:
            query: 搜索关键词
            memory_type: 记忆类型过滤
            min_confidence: 最小置信度
            limit: 最大返回数量
            mode: 搜索模式

        Returns:
            记忆列表
        """
        if mode == "keyword" or not query:
            return self._keyword_search(query, memory_type, min_confidence, limit)

        if mode == "semantic":
            return self._semantic_search(query, memory_type, min_confidence, limit)

        return self._hybrid_search(query, memory_type, min_confidence, limit)

    def _keyword_search(
        self, query: str, memory_type: Optional[str], min_confidence: float, limit: int
    ) -> List[Dict[str, Any]]:
        """关键词搜索"""
        sql = "SELECT id, type, content, tags, confidence, source, status, created_at FROM memories WHERE status='active' AND confidence>=?"
        params: List[Any] = [min_confidence]

        if memory_type:
            sql += " AND type=?"
            params.append(memory_type)

        if query:
            sql += " AND (content LIKE ? OR tags LIKE ?)"
            params += [f"%{query}%", f"%{query}%"]

        sql += " ORDER BY confidence DESC LIMIT ?"
        params.append(limit)

        return [
            {
                "memory_id": r[0],
                "memory_type": r[1],
                "content": r[2],
                "tags": json.loads(r[3]),
                "confidence": r[4],
                "source": r[5],
                "status": r[6],
                "created_at": r[7],
            }
            for r in self.conn.execute(sql, params).fetchall()
        ]

    def _semantic_search(
        self, query: str, memory_type: Optional[str], min_confidence: float, limit: int
    ) -> List[Dict[str, Any]]:
        """语义搜索

        从数据库加载所有符合条件的记忆，用向量相似度排序
        """
        sql = "SELECT id, type, content, tags, confidence, source, status, created_at, embedding FROM memories WHERE status='active' AND confidence>=?"
        params: List[Any] = [min_confidence]

        if memory_type:
            sql += " AND type=?"
            params.append(memory_type)

        sql += " ORDER BY confidence DESC"

        rows = self.conn.execute(sql, params).fetchall()
        query_vec = embedding_vector(query)

        scored = []
        for r in rows:
            embedding_str = r[8]
            if embedding_str:
                mem_vec = json.loads(embedding_str)
                score = cosine_similarity(query_vec, mem_vec)
            else:
                score = 0.0

            scored.append(
                (
                    score,
                    {
                        "memory_id": r[0],
                        "memory_type": r[1],
                        "content": r[2],
                        "tags": json.loads(r[3]),
                        "confidence": r[4],
                        "source": r[5],
                        "status": r[6],
                        "created_at": r[7],
                        "semantic_score": score,
                    },
                )
            )

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    def _hybrid_search(
        self, query: str, memory_type: Optional[str], min_confidence: float, limit: int
    ) -> List[Dict[str, Any]]:
        """混合搜索：关键词 + 语义加权"""

        keyword_results = self._keyword_search(query, memory_type, min_confidence, limit * 2)
        semantic_results = self._semantic_search(query, memory_type, min_confidence, limit * 2)

        # 合并去重，加权排序
        seen = set()
        merged = []

        # 关键词结果权重 0.8，语义结果权重 0.7
        for item in keyword_results:
            mid = item["memory_id"]
            if mid not in seen:
                seen.add(mid)
                item["combined_score"] = item.get("confidence", 0.5) * 0.8
                merged.append(item)

        for item in semantic_results:
            mid = item["memory_id"]
            if mid not in seen:
                seen.add(mid)
                item["combined_score"] = item.get("semantic_score", 0) * 0.7
                merged.append(item)
            else:
                # 已有，加权
                for existing in merged:
                    if existing["memory_id"] == mid:
                        existing["combined_score"] = max(
                            existing.get("combined_score", 0),
                            item.get("semantic_score", 0) * 0.7,
                        )
                        break

        merged.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
        return merged[:limit]

    def writeback_from_task(self, goal: Dict[str, Any], summary: Dict[str, Any]) -> List[str]:
        """从任务写入记忆"""
        gid = goal.get("goal_id", "goal_unknown")

        records = [
            MemoryRecord(
                memory_id=f"episodic_{gid}",
                memory_type="episodic",
                content=json.dumps(summary, ensure_ascii=False),
                tags=["task", gid],
                confidence=0.8,
                source="task_graph",
            )
        ]

        if summary.get("success"):
            records.append(
                MemoryRecord(
                    memory_id=f"procedural_success_{gid}",
                    memory_type="procedural",
                    content="reuse goal->judge->task_graph->verify->memory flow",
                    tags=["procedure", gid],
                    confidence=0.65,
                    source="task_graph",
                )
            )

        return [self.add(record) for record in records]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self.conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        by_type = self.conn.execute(
            "SELECT type, COUNT(*) FROM memories GROUP BY type"
        ).fetchall()
        active = self.conn.execute(
            "SELECT COUNT(*) FROM memories WHERE status='active'"
        ).fetchone()[0]
        with_embeddings = self.conn.execute(
            "SELECT COUNT(*) FROM memories WHERE embedding IS NOT NULL"
        ).fetchone()[0]

        return {
            "total": total,
            "active": active,
            "with_embeddings": with_embeddings,
            "by_type": dict(by_type),
        }


# 向后兼容
PersonalMemoryKernel = VectorMemoryKernel
MemoryRecord_old = MemoryRecord
