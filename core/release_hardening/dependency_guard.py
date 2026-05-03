from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path
from typing import List
from .schemas import DependencyCheck, CheckStatus, new_id
from .storage import JsonStore


class DependencyGuard:
    """V129: dependency availability and isolation guard."""

    DEFAULT_MODULES = ["json", "pathlib", "dataclasses", "typing"]

    def __init__(self, root: str | Path = ".release_hardening_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "dependency_checks.json")

    def check_one(self, module_name: str) -> DependencyCheck:
        spec = find_spec(module_name)
        available = spec is not None
        source = getattr(spec, "origin", "") if spec else ""
        status = CheckStatus.PASS if available else CheckStatus.FAIL
        notes = []
        if source and "site-packages" in source:
            notes.append("external_dependency")
        elif source:
            notes.append("stdlib_or_local")
        return DependencyCheck(
            id=new_id("dep"),
            module_name=module_name,
            available=available,
            source=source or "not_found",
            status=status,
            notes=notes,
        )

    def check_all(self, modules: List[str] | None = None) -> List[DependencyCheck]:
        modules = modules or self.DEFAULT_MODULES
        results = [self.check_one(x) for x in modules]
        self.store.write([
            {
                "id": r.id,
                "module_name": r.module_name,
                "available": r.available,
                "source": r.source,
                "status": r.status.value,
                "notes": r.notes,
            }
            for r in results
        ])
        return results

    def overall_status(self, results: List[DependencyCheck]) -> CheckStatus:
        return CheckStatus.FAIL if any(not r.available for r in results) else CheckStatus.PASS
