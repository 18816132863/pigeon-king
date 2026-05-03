from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import hashlib
from .schemas import SnapshotRecord, SnapshotStatus, new_id
from .storage import JsonStore


class SnapshotManager:
    """V130: lightweight manifest snapshot before upgrade."""

    SKIP_PARTS = {"__pycache__", ".pytest_cache", ".git", "node_modules", ".venv", "venv"}

    def __init__(self, root: str | Path = ".", state_root: str | Path = ".release_hardening_state"):
        self.root = Path(root)
        self.state_root = Path(state_root)
        self.store = JsonStore(self.state_root / "snapshots.json")

    def create_manifest(self, include_prefixes: List[str] | None = None) -> SnapshotRecord:
        prefixes = include_prefixes or ["core", "agent_kernel", "scripts", "tests", "docs"]
        files = []
        for prefix in prefixes:
            base = self.root / prefix
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if not p.is_file():
                    continue
                if any(part in self.SKIP_PARTS for part in p.parts):
                    continue
                if p.stat().st_size > 2_000_000:
                    continue
                rel = p.relative_to(self.root).as_posix()
                digest = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
                files.append({"path": rel, "size": p.stat().st_size, "sha256_16": digest})
        manifest_path = self.state_root / f"snapshot_{new_id('manifest')}.json"
        JsonStore(manifest_path).write({"files": files})
        record = SnapshotRecord(
            id=new_id("snapshot"),
            root=str(self.root.resolve()),
            tracked_files=len(files),
            manifest_path=str(manifest_path),
            status=SnapshotStatus.CREATED if files else SnapshotStatus.EMPTY,
        )
        self.store.append({
            "id": record.id,
            "root": record.root,
            "tracked_files": record.tracked_files,
            "manifest_path": record.manifest_path,
            "status": record.status.value,
            "created_at": record.created_at,
        })
        return record
