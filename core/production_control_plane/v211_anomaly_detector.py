from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class AnomalyDetector:
    """V211: simple anomaly detector."""
    def detect(self, values: list[float]) -> ControlArtifact:
        if not values:
            return ControlArtifact(new_id("anomaly"), "anomaly_detection", "anomaly", PlaneStatus.WARN, 0.5, {"anomalies": []})
        avg = sum(values) / len(values)
        anomalies = [v for v in values if avg and v > avg * 2.5]
        status = PlaneStatus.WARN if anomalies else PlaneStatus.READY
        return ControlArtifact(new_id("anomaly"), "anomaly_detection", "anomaly", status, 0.8 if anomalies else 0.94, {"avg": round(avg, 4), "anomalies": anomalies})
