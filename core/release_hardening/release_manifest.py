from __future__ import annotations

from pathlib import Path
from typing import List
from .schemas import ReleaseManifest, CheckStatus, new_id
from .storage import JsonStore


class ReleaseManifestBuilder:
    """V133: manifest builder for upgrade packages."""

    def __init__(self, root: str | Path = "."):
        self.root = Path(root)

    def build(self, version_from: str = "V126", version_to: str = "V136") -> ReleaseManifest:
        modules = sorted(str(p.relative_to(self.root)) for p in (self.root / "core" / "release_hardening").glob("*.py")) if (self.root / "core" / "release_hardening").exists() else []
        scripts = sorted(str(p.relative_to(self.root)) for p in (self.root / "scripts").glob("v127_v136_*.py")) if (self.root / "scripts").exists() else []
        tests = sorted(str(p.relative_to(self.root)) for p in (self.root / "tests").glob("test_v127_v136*.py")) if (self.root / "tests").exists() else []
        docs = sorted(str(p.relative_to(self.root)) for p in (self.root / "docs").glob("V127_V136*.md")) if (self.root / "docs").exists() else []
        status = CheckStatus.PASS if modules and scripts else CheckStatus.WARN
        return ReleaseManifest(
            id=new_id("release_manifest"),
            version_from=version_from,
            version_to=version_to,
            modules=modules,
            scripts=scripts,
            tests=tests,
            docs=docs,
            status=status,
        )
