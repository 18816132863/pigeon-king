from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import MemoryConsolidationReport, MemoryConsolidationStatus, new_id, to_dict
from .storage import JsonStore


class MemoryConsolidator:
    """V123: compact episodic/procedural memory into summary keys."""

    def __init__(self, root: str | Path = ".operating_spine_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "memory_consolidation_reports.json")

    def consolidate(self, records: List[Dict]) -> MemoryConsolidationReport:
        before = len(records)
        if before == 0:
            report = MemoryConsolidationReport(
                id=new_id("memcon"),
                status=MemoryConsolidationStatus.NOOP,
                before_count=0,
                after_count=0,
                summary_keys=[],
                review_notes=["no records"],
            )
            self.store.append(to_dict(report))
            return report

        grouped = {}
        for r in records:
            key = r.get("kind") or r.get("type") or "general"
            grouped.setdefault(key, []).append(r)

        summary_keys = sorted(grouped)
        after = len(summary_keys)
        status = MemoryConsolidationStatus.NEEDS_REVIEW if before > 200 else MemoryConsolidationStatus.COMPACTED
        notes = []
        if before > 200:
            notes.append("large memory volume; human review recommended before deleting raw records")

        report = MemoryConsolidationReport(
            id=new_id("memcon"),
            status=status,
            before_count=before,
            after_count=after,
            summary_keys=summary_keys,
            review_notes=notes,
        )
        self.store.append(to_dict(report))
        return report
