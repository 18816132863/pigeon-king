from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .self_diagnostics import SelfDiagnostics


@dataclass
class GateResult:
    status: str
    score: int
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    decision: str = "block"

    def to_dict(self) -> dict:
        return self.__dict__


class PerfectionGate:
    """Release gate for V10 autonomous OS agent.

    This is strict for offline consistency, but it does not claim real-world perfection:
    real device/API/account authorization must still be validated in the target runtime.
    """

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def evaluate(self) -> GateResult:
        report = SelfDiagnostics(self.root).run()
        blockers = [f"{f.name}: {f.detail}" for f in report.findings if f.severity == "error"]
        warnings = [f"{f.name}: {f.detail}" for f in report.findings if f.severity == "warning"]
        score = 100 - len(blockers) * 20 - len(warnings) * 5
        score = max(0, min(100, score))
        return GateResult(
            status="pass" if not blockers else "fail",
            score=score,
            blockers=blockers,
            warnings=warnings,
            decision="release_candidate" if not blockers else "block",
        )
