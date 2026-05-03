from __future__ import annotations

from pathlib import Path
from .schemas import CompatibilityReport, CompatibilityStatus, new_id


class CompatibilityShim:
    """V145: compatibility adapter across V85-V136 layers.

    In a full workspace, all layers should be present and status becomes
    COMPATIBLE. In an isolated patch package, only this layer may exist; that is
    PARTIAL rather than INCOMPATIBLE so the patch can verify before coverage.
    """

    LAYERS = {
        "v85_llm": "core/llm/__init__.py",
        "v86_personal_agent": "core/personal_agent/__init__.py",
        "v87_v96_autonomy": "core/autonomy/__init__.py",
        "v97_v106_operating_agent": "core/operating_agent/__init__.py",
        "v107_v116_self_evolution_ops": "core/self_evolution_ops/__init__.py",
        "v117_v126_operating_spine": "core/operating_spine/__init__.py",
        "v127_v136_release_hardening": "core/release_hardening/__init__.py",
        "v137_v146_runtime_activation": "core/runtime_activation/__init__.py",
    }

    def __init__(self, root: str | Path = "."):
        self.root = Path(root)

    def check(self) -> CompatibilityReport:
        layers = {name: (self.root / path).exists() for name, path in self.LAYERS.items()}
        missing = [k for k, v in layers.items() if not v]
        present_count = sum(1 for v in layers.values() if v)

        if not missing:
            status = CompatibilityStatus.COMPATIBLE
            fallback = "no fallback needed"
        elif layers.get("v137_v146_runtime_activation", False) and present_count >= 1:
            status = CompatibilityStatus.PARTIAL
            fallback = "isolated patch mode; after applying to full workspace, recheck should become compatible or high-partial"
        else:
            status = CompatibilityStatus.INCOMPATIBLE
            fallback = "install runtime_activation layer before activation"

        return CompatibilityReport(
            id=new_id("compat"),
            layers=layers,
            status=status,
            missing_layers=missing,
            fallback_plan=fallback,
        )
