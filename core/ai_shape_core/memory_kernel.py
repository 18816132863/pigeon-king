from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from .schemas import MemoryRecord, MemoryKind, new_id, to_dict
from .storage import JsonStore

class UnifiedMemoryKernel:
    """Unified memory kernel: short, long, semantic, episodic, and procedural memory."""

    def __init__(self, root: str | Path = ".ai_shape_core_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "unified_memory.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.store.read([]):
            return
        defaults = [
            MemoryRecord(new_id("mem"), MemoryKind.PROCEDURAL, "delivery.one_shot_package", "用户偏好：直接给完整压缩包 + 一条命令，不要一点点修。", 0.96, "observed_preference"),
            MemoryRecord(new_id("mem"), MemoryKind.SEMANTIC, "project.ai_shape", "目标形态：目标内核 + 记忆内核 + 法典裁判 + 世界接口 + 任务图执行器 + 能力自扩展。", 0.94, "ai_shape_report"),
            MemoryRecord(new_id("mem"), MemoryKind.PROCEDURAL, "risk.high_risk", "外部发送、删除、安装、付款、密钥等高风险操作必须审批或阻断。", 0.95, "governance_policy"),
            MemoryRecord(new_id("mem"), MemoryKind.LONG_TERM, "project.pigeon_king", "V85-V316 已形成大量平台模块，但需要 AI_SHAPE_CORE 收束成唯一主链。", 0.9, "conversation"),
        ]
        self.store.write([to_dict(x) for x in defaults])

    def write(self, kind: MemoryKind, key: str, value: Any, confidence: float, source: str) -> MemoryRecord:
        rec = MemoryRecord(new_id("mem"), kind, key, value, confidence, source)
        self.store.append(to_dict(rec))
        return rec

    def search(self, query: str, limit: int = 8) -> List[MemoryRecord]:
        q = query.lower()
        raw = self.store.read([])
        scored = []
        for item in raw:
            text = f"{item.get('key','')} {item.get('value','')} {item.get('source','')}".lower()
            score = 0
            for token in set(q.replace("，", " ").replace(",", " ").split()):
                if token and token in text:
                    score += 1
            if any(x in text for x in ["压缩包", "一条命令", "ai_shape", "目标内核", "高风险", "审批"]):
                score += 2
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._from_dict(x) for s, x in scored[:limit] if s > 0] or [self._from_dict(x) for _, x in scored[:min(limit, len(scored))]]

    def _from_dict(self, item: Dict) -> MemoryRecord:
        return MemoryRecord(
            id=item["id"],
            kind=MemoryKind(item["kind"]),
            key=item["key"],
            value=item.get("value"),
            confidence=float(item.get("confidence", 0.5)),
            source=item.get("source", ""),
            created_at=float(item.get("created_at", 0.0)),
        )
