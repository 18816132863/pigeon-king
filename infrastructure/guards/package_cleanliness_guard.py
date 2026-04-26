from __future__ import annotations

from pathlib import Path


class PackageCleanlinessGuard:
    BLOCKED_DIRS = {"repo", "logs", "__pycache__", ".pytest_cache", "site-packages", ".venv", "venv", ".git"}
    BLOCKED_SUFFIXES = {".pyc", ".pyo", ".log"}

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def scan(self) -> dict:
        bad = []
        for p in self.root.rglob("*"):
            rel = p.relative_to(self.root).as_posix()
            if set(Path(rel).parts) & self.BLOCKED_DIRS:
                bad.append(rel)
            if p.is_file() and (p.suffix in self.BLOCKED_SUFFIXES or p.name.endswith(".jsonl")):
                bad.append(rel)
        return {"status": "pass" if not bad else "fail", "bad_count": len(bad), "bad_sample": bad[:20]}
