from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import EvidenceRecord, EvidenceKind, new_id, to_dict
from .storage import JsonStore


class EvidenceCapture:
    """V150: captures evidence for decisions and outputs."""

    def __init__(self, root: str | Path = ".action_bridge_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "evidence_records.json")

    def record(self, run_id: str, kind: EvidenceKind, title: str, content: Dict) -> EvidenceRecord:
        rec = EvidenceRecord(
            id=new_id("evidence"),
            run_id=run_id,
            kind=kind,
            title=title,
            content=content,
        )
        self.store.append(to_dict(rec))
        return rec

    def list_run(self, run_id: str) -> List[EvidenceRecord]:
        return [self._from_dict(x) for x in self.store.read([]) if x.get("run_id") == run_id]

    def _from_dict(self, item: Dict) -> EvidenceRecord:
        return EvidenceRecord(
            id=item["id"],
            run_id=item["run_id"],
            kind=EvidenceKind(item["kind"]),
            title=item["title"],
            content=dict(item.get("content", {})),
            created_at=float(item.get("created_at", 0.0)),
        )
