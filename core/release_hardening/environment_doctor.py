from __future__ import annotations

from pathlib import Path
import sys
from .schemas import EnvironmentCheck, CheckStatus, new_id


class EnvironmentDoctor:
    """V127: environment doctor for deployability checks."""

    def __init__(self, root: str | Path = "."):
        self.root = Path(root)

    def check(self) -> EnvironmentCheck:
        required = {
            "core": (self.root / "core").exists(),
            "agent_kernel": (self.root / "agent_kernel").exists(),
            "scripts": (self.root / "scripts").exists(),
            "tests": (self.root / "tests").exists(),
        }
        pycache_count = sum(1 for _ in self.root.rglob("__pycache__")) if self.root.exists() else 0
        notes = []
        if pycache_count:
            notes.append(f"pycache_present:{pycache_count}")
        missing = [k for k, v in required.items() if not v]
        if missing:
            status = CheckStatus.WARN
            notes.append(f"missing_dirs:{','.join(missing)}")
        else:
            status = CheckStatus.PASS

        return EnvironmentCheck(
            id=new_id("env"),
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            cwd=str(self.root.resolve()),
            pycache_count=pycache_count,
            required_dirs=required,
            status=status,
            notes=notes,
        )
