#!/usr/bin/env python3
"""
V25.1 — 记忆回写压缩器

功能:
- 对话上下文压缩时自动写入 memory_kernel
- 保留关键决策 / 任务图 / 用户偏好
- 下次启动可恢复上次会话上下文

架构位置: infrastructure / memory_writeback_compressor.py
依赖:     agent_kernel.memory_kernel.PersonalMemoryKernel
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from orchestration.agent_kernel.memory_kernel import MemoryRecord, PersonalMemoryKernel


@dataclass
class CompressedContext:
    """压缩后的上下文快照"""
    snapshot_id: str
    conversation_id: str
    compressed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    summary: str = ""
    key_decisions: List[Dict[str, Any]] = field(default_factory=list)
    task_graph_state: Optional[Dict[str, Any]] = None
    user_preferences: List[str] = field(default_factory=list)
    active_checkpoint: Optional[str] = None
    token_estimate: int = 0


class MemoryWritebackCompressor:
    """
    记忆回写压缩器
    在上下文压缩前将关键信息回写到 PersonalMemoryKernel
    """

    def __init__(
        self,
        memory_kernel: Optional[PersonalMemoryKernel] = None,
        db_path: str = ":memory:",
        min_confidence: float = 0.6,
    ):
        self.kernel = memory_kernel or PersonalMemoryKernel(db=db_path)
        self.min_confidence = min_confidence

    # ------------------------------------------------------------------
    # 压缩并回写
    # ------------------------------------------------------------------
    def compress_and_writeback(
        self,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        task_graph: Optional[Dict[str, Any]] = None,
        checkpoint_id: Optional[str] = None,
    ) -> CompressedContext:
        """
        压缩对话上下文并写入记忆

        Args:
            conversation_id: 会话 ID
            messages: 对话消息列表 [{"role": str, "content": str, ...}]
            task_graph: 当前任务图快照（可选）
            checkpoint_id: 当前 checkpoint ID（可选）

        Returns:
            CompressedContext: 压缩后的上下文快照
        """
        # 1. 生成摘要
        summary = self._summarize(messages)

        # 2. 提取关键决策
        decisions = self._extract_decisions(messages)

        # 3. 提取用户偏好
        prefs = self._extract_preferences(messages)

        # 4. 构建快照
        snapshot_id = f"snapshot_{'%x' % int(time.time())}"
        context = CompressedContext(
            snapshot_id=snapshot_id,
            conversation_id=conversation_id,
            summary=summary,
            key_decisions=decisions,
            task_graph_state=task_graph,
            user_preferences=prefs,
            active_checkpoint=checkpoint_id,
            token_estimate=sum(len(m.get("content", "")) // 4 for m in messages),
        )

        # 5. 写入记忆内核
        self._write_episodic(context)
        self._write_semantic(context)

        return context

    # ------------------------------------------------------------------
    # 恢复上一次快照
    # ------------------------------------------------------------------
    def recover_context(
        self, conversation_id: str
    ) -> Optional[CompressedContext]:
        """从记忆内核恢复上次的上下文快照"""
        memories = self.kernel.search(
            q=conversation_id,
            memory_type="episodic",
            min_confidence=self.min_confidence,
            limit=1,
        )
        if not memories:
            return None
        try:
            content = json.loads(memories[0]["content"])
            return CompressedContext(**content)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    def _summarize(self, messages: List[Dict[str, Any]]) -> str:
        """生成对话摘要"""
        if not messages:
            return ""
        parts: List[str] = []
        for msg in messages[-10:]:  # 最近 10 条
            role = msg.get("role", "?")
            content = msg.get("content", "")[:100]
            if len(content) >= 100:
                content = content[:97] + "..."
            parts.append(f"[{role}] {content}")
        return "\n".join(parts)

    def _extract_decisions(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """提取关键决策"""
        decisions: List[Dict[str, Any]] = []
        for msg in messages[-20:]:
            content = msg.get("content", "")
            if any(
                kw in content.lower()
                for kw in ["决定", "选择", "采用", "批准", "拒绝", "选"]
            ):
                decisions.append(
                    {
                        "source": msg.get("role", "?"),
                        "content": content[:200],
                        "timestamp": msg.get("timestamp", time.time()),
                    }
                )
        return decisions

    def _extract_preferences(
        self, messages: List[Dict[str, Any]]
    ) -> List[str]:
        """提取用户偏好"""
        prefs: List[str] = []
        for msg in messages:
            content = msg.get("content", "")
            if any(
                kw in content.lower()
                for kw in ["我喜欢", "我不喜欢", "帮我记住", "偏好", "习惯"]
            ):
                prefs.append(content[:200])
        return prefs

    def _write_episodic(self, context: CompressedContext) -> str:
        """写入经历性记忆"""
        content = json.dumps(asdict(context), ensure_ascii=False)
        record = MemoryRecord(
            memory_id=f"episodic_{context.snapshot_id}",
            memory_type="episodic",
            content=content,
            tags=["compressed_context", context.conversation_id],
            confidence=0.75,
            source="memory_writeback_compressor",
        )
        return self.kernel.add(record)

    def _write_semantic(self, context: CompressedContext) -> Optional[str]:
        """写入语义性记忆（如果有关键决策）"""
        if not context.key_decisions:
            return None
        decision_text = json.dumps(
            {"decisions": context.key_decisions, "summary": context.summary},
            ensure_ascii=False,
        )
        record = MemoryRecord(
            memory_id=f"semantic_decision_{context.snapshot_id}",
            memory_type="semantic",
            content=decision_text,
            tags=["decisions", context.conversation_id],
            confidence=0.8,
            source="memory_writeback_compressor",
        )
        return self.kernel.add(record)
