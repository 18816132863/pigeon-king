"""V84/V85 release freeze manifest."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping


@dataclass(frozen=True)
class ReleaseFreezeManifest:
    version: str = "V85.0"
    shape: str = "final_full_function_embodied_pending_access_state"
    live_world_connected: bool = False
    live_credentials_bound: bool = False
    live_payment_enabled: bool = False
    live_signature_enabled: bool = False
    live_external_send_enabled: bool = False
    live_physical_actuation_enabled: bool = False
    final_switch_scope: str = "adapter_credential_approval_config_only"
    frozen_boundaries: List[str] = field(default_factory=lambda: [
        "payment_hard_stop",
        "signature_hard_stop",
        "physical_actuation_hard_stop",
        "identity_commit_hard_stop",
        "destructive_action_hard_stop",
        "external_send_draft_or_approval_only",
        "memory_cannot_override_policy",
        "tool_content_is_untrusted_until_classified",
        "global_kill_switch_can_halt_all_runtime",
    ])
    reusable_strength_paths: List[str] = field(default_factory=lambda: [
        "digital_global_agent",
        "multimodal_creation_execution_engine",
        "explainable_governance_decision_center",
        "embodied_pending_access_kernel",
    ])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FreezeManifestGate:
    def evaluate(self, manifest: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        m = dict(manifest or ReleaseFreezeManifest().to_dict())
        checks = {
            "live_world_disconnected": m.get("live_world_connected") is False,
            "credentials_unbound": m.get("live_credentials_bound") is False,
            "payment_disabled": m.get("live_payment_enabled") is False,
            "signature_disabled": m.get("live_signature_enabled") is False,
            "external_send_disabled": m.get("live_external_send_enabled") is False,
            "physical_actuation_disabled": m.get("live_physical_actuation_enabled") is False,
            "final_switch_scope_limited": m.get("final_switch_scope") == "adapter_credential_approval_config_only",
            "has_enough_frozen_boundaries": len(m.get("frozen_boundaries") or []) >= 8,
            "other_paths_preserved": set(m.get("reusable_strength_paths") or []) >= {"digital_global_agent", "multimodal_creation_execution_engine", "explainable_governance_decision_center", "embodied_pending_access_kernel"},
        }
        return {"status": "pass" if all(checks.values()) else "fail", "checks": checks, "manifest": m}


def run_freeze_manifest_gate() -> Dict[str, Any]:
    return FreezeManifestGate().evaluate()
