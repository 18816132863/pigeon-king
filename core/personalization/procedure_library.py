from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import ProcedureTemplate, new_id, to_dict
from .storage import JsonStore


class ProcedureLibrary:
    """V161: reusable user-specific procedures."""

    def __init__(self, root: str | Path = ".personalization_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "procedure_templates.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.store.read([]):
            return
        procedures = [
            ProcedureTemplate(
                id=new_id("procedure"),
                name="one_shot_upgrade_package",
                trigger_keywords=["继续", "推进", "版本", "压缩包", "命令"],
                steps=["define next 10 features", "create patch package", "add apply script", "add verify script", "run local verification", "send one command"],
                success_count=8,
                confidence=0.92,
            ),
            ProcedureTemplate(
                id=new_id("procedure"),
                name="high_risk_approval_flow",
                trigger_keywords=["发送", "删除", "安装", "转账", "客户"],
                steps=["compile action", "classify risk", "dry-run", "create handoff", "wait approval", "resume from checkpoint"],
                success_count=5,
                confidence=0.88,
            ),
        ]
        self.store.write([to_dict(p) for p in procedures])

    def select(self, goal: str) -> ProcedureTemplate:
        procedures = [self._from_dict(x) for x in self.store.read([])]
        scored = []
        for p in procedures:
            score = p.confidence + sum(1 for kw in p.trigger_keywords if kw in goal) * 0.2
            scored.append((score, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    def record_result(self, procedure_id: str, success: bool) -> ProcedureTemplate:
        data = self.store.read([])
        for item in data:
            if item["id"] == procedure_id:
                item["success_count"] = int(item.get("success_count", 0)) + (1 if success else 0)
                item["failure_count"] = int(item.get("failure_count", 0)) + (0 if success else 1)
                total = item["success_count"] + item["failure_count"]
                item["confidence"] = round(item["success_count"] / max(1, total), 4)
                self.store.write(data)
                return self._from_dict(item)
        raise KeyError(f"unknown procedure_id: {procedure_id}")

    def _from_dict(self, item: Dict) -> ProcedureTemplate:
        return ProcedureTemplate(
            id=item["id"],
            name=item["name"],
            trigger_keywords=list(item.get("trigger_keywords", [])),
            steps=list(item.get("steps", [])),
            success_count=int(item.get("success_count", 0)),
            failure_count=int(item.get("failure_count", 0)),
            confidence=float(item.get("confidence", 0.6)),
        )
