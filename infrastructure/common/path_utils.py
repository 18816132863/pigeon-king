"""Workspace path helpers.

V108.2: avoid fragile ``Path.cwd()`` based roots.  The resolver walks upward
from this file and falls back to the current directory only if no workspace
markers are found.  This makes gates, hooks, and local search stable even when
called from a non-workspace cwd.
"""
from __future__ import annotations

import os
from pathlib import Path

_MARKERS = (
    "openclaw.json", "AGENTS.md", "skills", "governance", "orchestration", "infrastructure"
)


def _has_workspace_markers(path: Path) -> bool:
    score = 0
    for marker in _MARKERS:
        if (path / marker).exists():
            score += 1
    return score >= 3


def get_workspace_root(start: str | Path | None = None) -> Path:
    env_root = os.environ.get("OPENCLAW_WORKSPACE") or os.environ.get("WORKSPACE_ROOT")
    if env_root:
        p = Path(env_root).expanduser().resolve()
        if p.exists():
            return p
    base = Path(start).resolve() if start else Path(__file__).resolve()
    if base.is_file():
        base = base.parent
    for candidate in [base, *base.parents]:
        if _has_workspace_markers(candidate):
            return candidate
    return Path.cwd().resolve()


def resolve_workspace_path(*parts: str | Path) -> Path:
    return get_workspace_root() / Path(*parts)
