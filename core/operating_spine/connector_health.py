from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import ConnectorHealthReport, ConnectorHealthStatus, new_id, to_dict
from .storage import JsonStore


class ConnectorHealthMonitor:
    """V122: connector health monitor and degradation policy."""

    def __init__(self, root: str | Path = ".operating_spine_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "connector_health_reports.json")

    def check(self, connector_name: str, latency_ms: int = 80, failure_rate: float = 0.0) -> ConnectorHealthReport:
        if failure_rate >= 0.5 or latency_ms >= 5000:
            status = ConnectorHealthStatus.OFFLINE
            recommendation = "disable connector and use fallback"
        elif failure_rate >= 0.15 or latency_ms >= 1500:
            status = ConnectorHealthStatus.DEGRADED
            recommendation = "route only low-risk calls and prefer fallback"
        else:
            status = ConnectorHealthStatus.HEALTHY
            recommendation = "connector can be used"

        report = ConnectorHealthReport(
            id=new_id("health"),
            connector_name=connector_name,
            status=status,
            latency_ms=latency_ms,
            failure_rate=failure_rate,
            recommendation=recommendation,
        )
        self.store.append(to_dict(report))
        return report

    def healthy_count(self) -> int:
        return sum(1 for item in self.store.read([]) if item.get("status") == ConnectorHealthStatus.HEALTHY.value)
