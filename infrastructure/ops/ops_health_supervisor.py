from __future__ import annotations

from .connector_uptime_monitor import ConnectorUptimeMonitor
from .drift_detector import DriftDetector
from .incident_manager import IncidentManager


class OpsHealthSupervisor:
    """Operational supervisor for continuous autonomy."""

    def __init__(self) -> None:
        self.uptime = ConnectorUptimeMonitor()
        self.drift = DriftDetector()
        self.incident = IncidentManager()

    def supervise(self, baseline: dict, current: dict, connectors: list[dict]) -> dict:
        drift = self.drift.detect(baseline, current)
        uptime = self.uptime.check_many(connectors)
        incident = None
        if drift["requires_review"] or uptime["unhealthy_count"] > 0:
            incident = self.incident.open_incident("runtime_health_attention_required", "warning")
        return {
            "status": "supervised",
            "drift": drift,
            "uptime": uptime,
            "incident": incident,
        }
