"""V12.0 Release Manifest and final local gate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from infrastructure.acceptance_matrix import run_acceptance_matrix
from infrastructure.ops_health import build_health_report


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_file_manifest(root: str | Path = ".", *, include_suffixes: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    root = Path(root).resolve()
    suffixes = set(include_suffixes or [".py", ".md", ".txt"])
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if any(part in {"__pycache__", ".pytest_cache", ".git"} for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        files.append({"path": rel, "bytes": path.stat().st_size, "sha256": _sha256(path)})
    digest = hashlib.sha256(json.dumps(files, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {"root": str(root), "digest": digest, "files": files, "file_count": len(files)}


def build_release_manifest(*, root: str | Path = ".", db_path: Optional[Path] = None) -> Dict[str, Any]:
    acceptance = run_acceptance_matrix(db_path=db_path)
    health = build_health_report(db_path=db_path)
    files = collect_file_manifest(root)
    blocking = []
    if acceptance["gate"] != "pass":
        blocking.append("acceptance_matrix_failed")
    if health["release_gate"] not in {"pass", "warn"}:
        blocking.append("health_gate_failed")
    return {
        "version": "V12.0",
        "release_gate": "pass" if not blocking else "fail",
        "blocking_items": blocking,
        "acceptance": acceptance,
        "health": health,
        "file_manifest": files,
    }


def write_release_manifest(path: str | Path = "V12_0_RELEASE_MANIFEST.json", *, root: str | Path = ".", db_path: Optional[Path] = None) -> Dict[str, Any]:
    manifest = build_release_manifest(root=root, db_path=db_path)
    Path(path).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
