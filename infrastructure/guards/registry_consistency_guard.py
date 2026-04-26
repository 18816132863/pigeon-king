from __future__ import annotations

from pathlib import Path
import json


class RegistryConsistencyGuard:
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def check_module_registry(self) -> dict:
        path = self.root / "infrastructure" / "inventory" / "module_registry.json"
        if not path.exists():
            return {"status": "fail", "reason": "module_registry_missing"}
        data = json.loads(path.read_text(encoding="utf-8"))
        modules = data.get("modules", {})
        stats_total = data.get("stats", {}).get("total")
        return {
            "status": "pass" if stats_total == len(modules) else "fail",
            "actual": len(modules),
            "stats_total": stats_total,
        }

    def check_fusion_index(self) -> dict:
        path = self.root / "infrastructure" / "inventory" / "fusion_index.json"
        if not path.exists():
            return {"status": "fail", "reason": "fusion_index_missing"}
        text = path.read_text(encoding="utf-8")
        return {"status": "pass" if "275" not in text else "fail", "contains_old_275": "275" in text}
