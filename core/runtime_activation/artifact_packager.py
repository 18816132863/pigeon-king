from __future__ import annotations

from pathlib import Path
from .schemas import ArtifactPackageRecord, PackageStatus, new_id


class ArtifactPackager:
    """V144: artifact package manifest generator.

    It does not zip the whole workspace; it records what should be packaged.
    Actual compression remains in release scripts.
    """

    def __init__(self, root: str | Path = "."):
        self.root = Path(root)

    def build_record(self, package_name: str, prefixes: list[str] | None = None) -> ArtifactPackageRecord:
        prefixes = prefixes or ["core/runtime_activation", "scripts", "tests", "docs"]
        files = []
        for prefix in prefixes:
            base = self.root / prefix
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
                    files.append(p.relative_to(self.root).as_posix())
        status = PackageStatus.CREATED if files else PackageStatus.EMPTY
        command = f"zip -r {package_name}.zip " + " ".join(prefixes)
        return ArtifactPackageRecord(
            id=new_id("artifact"),
            package_name=package_name,
            files=sorted(files),
            status=status,
            command=command,
            notes=[f"file_count:{len(files)}"],
        )
