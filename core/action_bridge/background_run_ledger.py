from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import BackgroundRunRecord, BackgroundRunStatus, new_id, to_dict
from .storage import JsonStore


class BackgroundRunLedger:
    """V154: background run ledger without claiming async execution."""

    def __init__(self, root: str | Path = ".action_bridge_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "background_runs.json")

    def create(self, title: str, checkpoint: Dict, waiting: bool = False) -> BackgroundRunRecord:
        rec = BackgroundRunRecord(
            id=new_id("bg"),
            title=title,
            status=BackgroundRunStatus.WAITING if waiting else BackgroundRunStatus.CREATED,
            checkpoint=checkpoint,
            resume_hint=f"resume from checkpoint {checkpoint.get('id', 'unknown')}",
        )
        self.store.append(to_dict(rec))
        return rec

    def mark(self, run_id: str, status: BackgroundRunStatus) -> BackgroundRunRecord:
        data = self.store.read([])
        for item in data:
            if item["id"] == run_id:
                item["status"] = status.value
                self.store.write(data)
                return self._from_dict(item)
        raise KeyError(f"unknown background run: {run_id}")

    def _from_dict(self, item: Dict) -> BackgroundRunRecord:
        return BackgroundRunRecord(
            id=item["id"],
            title=item["title"],
            status=BackgroundRunStatus(item["status"]),
            checkpoint=dict(item.get("checkpoint", {})),
            resume_hint=item.get("resume_hint", ""),
            created_at=float(item.get("created_at", 0.0)),
        )
