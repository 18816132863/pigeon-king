from __future__ import annotations

from pathlib import Path
from .schemas import StateInspectionReport, DiagnosticStatus, new_id


class StateInspector:
    """V141: inspect runtime state and installed layers."""

    LAYERS = {
        "llm": "core/llm",
        "personal_agent": "core/personal_agent",
        "autonomy": "core/autonomy",
        "operating_agent": "core/operating_agent",
        "self_evolution_ops": "core/self_evolution_ops",
        "operating_spine": "core/operating_spine",
        "release_hardening": "core/release_hardening",
        "runtime_activation": "core/runtime_activation",
    }

    def __init__(self, root: str | Path = "."):
        self.root = Path(root)

    def inspect(self) -> StateInspectionReport:
        modules = {k: (self.root / v / "__init__.py").exists() for k, v in self.LAYERS.items()}
        states = {
            "runtime_activation": (self.root / ".runtime_activation_state").exists(),
            "release_hardening": (self.root / ".release_hardening_state").exists(),
        }
        cache_count = sum(1 for _ in self.root.rglob("__pycache__")) if self.root.exists() else 0
        missing = [k for k, v in modules.items() if not v]
        if len(missing) >= 5:
            status = DiagnosticStatus.FAIL
        elif missing or cache_count:
            status = DiagnosticStatus.WARN
        else:
            status = DiagnosticStatus.PASS
        notes = [f"missing_layers:{','.join(missing)}"] if missing else []
        if cache_count:
            notes.append(f"cache_count:{cache_count}")
        return StateInspectionReport(
            id=new_id("inspect"),
            required_modules=modules,
            state_dirs=states,
            cache_count=cache_count,
            status=status,
            notes=notes,
        )
