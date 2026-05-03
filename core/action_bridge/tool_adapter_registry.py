from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import ToolAdapterSpec, AdapterStatus, ActionKind, ActionRisk, new_id, to_dict
from .storage import JsonStore


class ToolAdapterRegistry:
    """V149: maps action kinds to tool adapters."""

    def __init__(self, root: str | Path = ".action_bridge_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "tool_adapters.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.store.read([]):
            return
        adapters = [
            ToolAdapterSpec(new_id("adapter"), "read_adapter", ActionKind.READ.value, AdapterStatus.ACTIVE, ActionRisk.L1),
            ToolAdapterSpec(new_id("adapter"), "write_artifact_adapter", ActionKind.WRITE.value, AdapterStatus.ACTIVE, ActionRisk.L2),
            ToolAdapterSpec(new_id("adapter"), "external_send_draft_adapter", ActionKind.SEND.value, AdapterStatus.ACTIVE, ActionRisk.L3),
            ToolAdapterSpec(new_id("adapter"), "media_prompt_adapter", ActionKind.MEDIA_GENERATE.value, AdapterStatus.ACTIVE, ActionRisk.L2),
            ToolAdapterSpec(new_id("adapter"), "plan_adapter", ActionKind.PLAN_ONLY.value, AdapterStatus.ACTIVE, ActionRisk.L1),
            ToolAdapterSpec(new_id("adapter"), "install_sandbox_adapter", ActionKind.INSTALL.value, AdapterStatus.ACTIVE, ActionRisk.L4),
            ToolAdapterSpec(new_id("adapter"), "device_control_dry_adapter", ActionKind.DEVICE_CONTROL.value, AdapterStatus.ACTIVE, ActionRisk.L3),
        ]
        self.store.write([to_dict(x) for x in adapters])

    def select(self, action_kind: ActionKind) -> ToolAdapterSpec:
        for item in self.store.read([]):
            spec = self._from_dict(item)
            if spec.capability == action_kind.value and spec.status == AdapterStatus.ACTIVE:
                return spec
        return ToolAdapterSpec(
            id=new_id("adapter"),
            name="missing_adapter",
            capability=action_kind.value,
            status=AdapterStatus.MISSING,
            risk_limit=ActionRisk.L0,
            dry_run_supported=False,
        )

    def _from_dict(self, item: Dict) -> ToolAdapterSpec:
        return ToolAdapterSpec(
            id=item["id"],
            name=item["name"],
            capability=item["capability"],
            status=AdapterStatus(item["status"]),
            risk_limit=ActionRisk(item["risk_limit"]),
            dry_run_supported=bool(item.get("dry_run_supported", True)),
            metadata=dict(item.get("metadata", {})),
        )
