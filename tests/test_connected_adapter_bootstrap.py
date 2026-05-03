"""Tests for connected adapter bootstrap.

Note: The current ConnectedAdapterBootstrap is a simplified probe-only version
that returns device connection state and strategy. Tests exercise the core API.
"""

from __future__ import annotations

from infrastructure.connected_adapter_bootstrap import (
    AdapterStatus,
    ConnectedAdapterBootstrap,
    ConnectedAdapterConfig,
)


def test_bootstrap_defaults_to_connected_state() -> None:
    bootstrap = ConnectedAdapterBootstrap(probe_only=True)
    state = bootstrap.bootstrap()
    assert state.session_connected is True
    assert state.connected_runtime in {"partial", "ready", "local"}


def test_bootstrap_sets_strategy_for_connected_state() -> None:
    bootstrap = ConnectedAdapterBootstrap(probe_only=True, assume_session_connected=True)
    state = bootstrap.bootstrap()
    assert state.strategy is not None
    assert "default_mode" in state.strategy
    assert state.recovery_steps is not None


def test_adapter_status_is_valid_enum() -> None:
    assert AdapterStatus.LOADED.value == "loaded"
    assert AdapterStatus.PARTIAL.value == "partial"
    assert AdapterStatus.FAILED.value == "failed"


def test_connected_adapter_config_defaults() -> None:
    config = ConnectedAdapterConfig()
    assert config.probe_only is True
    assert config.assume_session_connected is True


def test_bootstrap_to_dict_serializable() -> None:
    bootstrap = ConnectedAdapterBootstrap(probe_only=True)
    state = bootstrap.bootstrap()
    d = state.to_dict()
    assert isinstance(d, dict)
    assert d["session_connected"] is True
