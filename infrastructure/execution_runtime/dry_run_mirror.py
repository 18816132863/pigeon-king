from __future__ import annotations
from typing import Any, Dict

class DryRunMirror:
    def mirror(self, action: dict | None = None) -> Dict[str, Any]:
        return {"status": "dry_run_mirror", "action": dict(action or {}), "real_side_effect": False}
