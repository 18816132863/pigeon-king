from __future__ import annotations

from infrastructure.connected_adapter_bootstrap import (
    AdapterStatus,
    ConnectedAdapterBootstrap,
    ConnectedAdapterConfig,
)


def test_bootstrap_defaults_to_session_connected() -> None:
    bootstrap = ConnectedAdapterBootstrap(ConnectedAdapterConfig(probe_only=True))
    state = bootstrap.bootstrap()
    assert state.session_connected is True
    assert state.connected_runtime in {"partial", "ready"}
    assert state.adapter_status in {AdapterStatus.PARTIAL, AdapterStatus.FAILED, AdapterStatus.LOADED}


def test_adapter_not_loaded_does_not_execute_l0_route() -> None:
    bootstrap = ConnectedAdapterBootstrap(ConnectedAdapterConfig(probe_only=True))
    state = bootstrap.bootstrap()
    state.adapter_loaded = False
    allowed, reason = bootstrap.should_execute_route("route.query_note", state)
    assert allowed is False
    assert reason == "adapter_not_loaded_recovery_required"


def test_safe_route_allowlist_blocks_dangerous_route() -> None:
    bootstrap = ConnectedAdapterBootstrap(ConnectedAdapterConfig(probe_only=True))
    state = bootstrap.bootstrap()
    state.adapter_loaded = True
    allowed, reason = bootstrap.should_execute_route("route.send_message", state)
    assert allowed is False
    assert reason == "route_not_in_l0_l1_safe_allowlist"


def test_probe_only_smoke_has_no_side_effect() -> None:
    def fake_probe(name: str, payload: dict) -> dict:
        return {"status": "ready", "name": name, "probe_only": payload.get("probe_only")}

    bootstrap = ConnectedAdapterBootstrap(
        ConnectedAdapterConfig(probe_only=True),
        device_tool_probe=fake_probe,
    )
    state = bootstrap.bootstrap()
    result = bootstrap.smoke_route("route.query_note", state)
    assert result["side_effect"] is False
    assert result["probe_only"] is True
    assert result["status"] in {"ok", "dry_run_ok"}


def test_recovery_chain_records_steps_without_real_adapter() -> None:
    bootstrap = ConnectedAdapterBootstrap(ConnectedAdapterConfig(probe_only=True))
    state = bootstrap.bootstrap()
    assert state.recovery_steps
    assert "reload_adapter" in state.recovery_steps
