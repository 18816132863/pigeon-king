from __future__ import annotations


class EnvironmentCapabilityProbe:
    """Probe what the current runtime can actually do, without side effects."""

    def probe(self, connectors: list[dict] | None = None, device_runtime: dict | None = None) -> dict:
        connectors = connectors or []
        device_runtime = device_runtime or {}
        ready_connectors = [c for c in connectors if c.get("status") in {"ready", "authorized"}]
        return {
            "status": "probed",
            "ready_connectors": ready_connectors,
            "missing_connectors": [c for c in connectors if c.get("status") not in {"ready", "authorized"}],
            "device_runtime_ready": bool(device_runtime.get("adapter_loaded") or device_runtime.get("runtime_ready")),
            "external_execution_possible": bool(ready_connectors) or bool(device_runtime.get("adapter_loaded")),
            "side_effect": False,
        }
