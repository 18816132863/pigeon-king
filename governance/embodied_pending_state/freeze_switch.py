"""Live-access freeze switch for the embodied-pending-access state."""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class LiveAccessState:
    live_world_access_enabled: bool
    live_credentials_enabled: bool
    live_actuator_enabled: bool
    payment_enabled: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_live_access_state(config: Mapping[str, Any] | None = None) -> LiveAccessState:
    config = dict(config or {})
    def flag(name: str) -> bool:
        if name in config:
            return bool(config[name])
        return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}

    # Intentionally independent switches. In the pending-access state all default to false.
    live_world = flag("XIAOYI_LIVE_WORLD_ACCESS")
    live_creds = flag("XIAOYI_LIVE_CREDENTIALS")
    live_actuator = flag("XIAOYI_LIVE_ACTUATOR")
    payment = flag("XIAOYI_PAYMENT_EXECUTION")
    reason = "pending_access_state_live_switches_default_closed"
    if any([live_world, live_creds, live_actuator, payment]):
        reason = "live_switch_requested_but_commit_barrier_still_requires_dual_control"
    return LiveAccessState(live_world, live_creds, live_actuator, payment, reason)


def assert_pending_access_frozen(config: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    state = get_live_access_state(config)
    ok = not any([
        state.live_world_access_enabled,
        state.live_credentials_enabled,
        state.live_actuator_enabled,
        state.payment_enabled,
    ])
    return {
        "ok": ok,
        "state": state.to_dict(),
        "required_state": "all_live_switches_false",
        "reason": "frozen" if ok else "live_switch_present_requires_manual_security_review",
    }
