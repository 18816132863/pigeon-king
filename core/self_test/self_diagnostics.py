from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class DiagnosticFinding:
    name: str
    status: str
    detail: str
    severity: str = "info"


@dataclass
class DiagnosticReport:
    status: str
    findings: list[DiagnosticFinding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning")

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "findings": [f.__dict__ for f in self.findings],
        }


class SelfDiagnostics:
    """Static and registry diagnostics that run without external services."""

    REQUIRED_V10_FILES = [
        "core/autonomy/goal_strategy_kernel.py",
        "core/autonomy/task_graph_compiler.py",
        "governance/codex/personal_codex.py",
        "governance/codex/judgement_engine.py",
        "memory_context/personalization/personalization_engine.py",
        "infrastructure/external_capability_bus.py",
        "infrastructure/solution_search_orchestrator.py",
        "infrastructure/capability_self_extension.py",
        "orchestration/personal_autonomous_os_agent.py",
        "core/self_test/system_self_test_agent.py",
        "core/self_test/perfection_gate.py",
    ]

    POLLUTION_NAMES = {
        "repo",
        "logs",
        "__pycache__",
        ".pytest_cache",
        "site-packages",
        ".venv",
        "venv",
        ".git",
    }

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(self) -> DiagnosticReport:
        findings: list[DiagnosticFinding] = []
        findings.extend(self._check_required_files())
        findings.extend(self._check_pollution())
        findings.extend(self._check_registry_consistency())
        status = "pass" if not any(f.severity == "error" for f in findings) else "fail"
        return DiagnosticReport(status=status, findings=findings)

    def _check_required_files(self) -> list[DiagnosticFinding]:
        out = []
        for rel in self.REQUIRED_V10_FILES:
            exists = (self.root / rel).exists()
            out.append(DiagnosticFinding(
                name=f"required_file:{rel}",
                status="pass" if exists else "fail",
                detail="present" if exists else "missing",
                severity="info" if exists else "error",
            ))
        return out

    def _check_pollution(self) -> list[DiagnosticFinding]:
        pollution = []
        for p in self.root.rglob("*"):
            rel = p.relative_to(self.root).as_posix()
            parts = set(Path(rel).parts)
            if parts & self.POLLUTION_NAMES:
                pollution.append(rel)
            if p.is_file() and (p.suffix in {".pyc", ".pyo", ".log"} or p.name.endswith(".jsonl")):
                pollution.append(rel)
        return [DiagnosticFinding(
            name="clean_package_pollution",
            status="pass" if not pollution else "fail",
            detail=f"pollution_count={len(pollution)}",
            severity="info" if not pollution else "error",
        )]

    def _check_registry_consistency(self) -> list[DiagnosticFinding]:
        out: list[DiagnosticFinding] = []
        inv = self.root / "infrastructure" / "inventory"

        skill_registry = inv / "skill_registry.json"
        skill_inverted = inv / "skill_inverted_index.json"
        fusion = inv / "fusion_index.json"
        module_registry = inv / "module_registry.json"

        if skill_registry.exists():
            data = json.loads(skill_registry.read_text(encoding="utf-8"))
            count = len(data.get("skills", data.get("items", {})))
            out.append(DiagnosticFinding("skill_registry_count", "pass", f"skills={count}", "info" if count >= 100 else "warning"))

        if skill_inverted.exists():
            data = json.loads(skill_inverted.read_text(encoding="utf-8"))
            total = data.get("stats", {}).get("total")
            out.append(DiagnosticFinding("skill_inverted_total", "pass" if total in {None, 201} or isinstance(total, int) else "fail", f"total={total}", "info"))

        if fusion.exists():
            data = json.loads(fusion.read_text(encoding="utf-8"))
            skills_total = data.get("skills", {}).get("total") or data.get("indexes", {}).get("skills", {}).get("total")
            old_275 = "275" in fusion.read_text(encoding="utf-8")
            out.append(DiagnosticFinding("fusion_index_skill_total", "pass" if not old_275 else "fail", f"skills_total={skills_total}, has_275={old_275}", "info" if not old_275 else "error"))

        if module_registry.exists():
            data = json.loads(module_registry.read_text(encoding="utf-8"))
            modules = data.get("modules", {})
            stats_total = data.get("stats", {}).get("total")
            ok = stats_total == len(modules)
            out.append(DiagnosticFinding("module_registry_stats", "pass" if ok else "fail", f"stats_total={stats_total}, actual={len(modules)}", "info" if ok else "error"))

        return out
