from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import hashlib
import re

from .schemas import PluginSandboxReport, new_id, dataclass_to_dict
from .storage import JsonStore


class PluginSandboxManager:
    """V101: plugin sandbox and promotion gate.

    It performs deterministic static checks and simulated tests. It does NOT
    install or execute unknown code directly.
    """

    FORBIDDEN_PATTERNS = [
        r"os\.system",
        r"subprocess\.",
        r"eval\(",
        r"exec\(",
        r"rm\s+-rf",
        r"open\(.+['\"]w",
        r"requests\..+http",
        r"socket\.",
    ]

    def __init__(self, root: str | Path = ".operating_agent_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "plugin_sandbox_reports.json")

    def evaluate_source(self, plugin_name: str, source_ref: str, source_text: str, has_rollback: bool = True, test_passed: bool = True) -> PluginSandboxReport:
        hits = []
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, source_text, flags=re.I):
                hits.append(pattern)

        static_safe = not hits
        digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()[:16]
        score = 0.0
        score += 0.45 if static_safe else 0.0
        score += 0.25 if has_rollback else 0.0
        score += 0.25 if test_passed else 0.0
        score += 0.05 if source_ref.startswith(("builtin://", "catalog://", "mcp://")) else 0.0
        promoted = score >= 0.9

        report = PluginSandboxReport(
            id=new_id("sandbox"),
            plugin_name=plugin_name,
            source_ref=source_ref,
            static_safe=static_safe,
            forbidden_hits=hits,
            has_rollback=has_rollback,
            test_passed=test_passed,
            promoted=promoted,
            score=round(score, 4),
            notes=[f"sha256:{digest}", "promotion_allowed" if promoted else "promotion_denied"],
        )
        self.store.append(dataclass_to_dict(report))
        return report

    def latest(self) -> PluginSandboxReport | None:
        data = self.store.read([])
        if not data:
            return None
        return self._from_dict(data[-1])

    def _from_dict(self, item: Dict) -> PluginSandboxReport:
        return PluginSandboxReport(
            id=item["id"],
            plugin_name=item["plugin_name"],
            source_ref=item["source_ref"],
            static_safe=bool(item.get("static_safe", False)),
            forbidden_hits=list(item.get("forbidden_hits", [])),
            has_rollback=bool(item.get("has_rollback", False)),
            test_passed=bool(item.get("test_passed", False)),
            promoted=bool(item.get("promoted", False)),
            score=float(item.get("score", 0.0)),
            notes=list(item.get("notes", [])),
        )
