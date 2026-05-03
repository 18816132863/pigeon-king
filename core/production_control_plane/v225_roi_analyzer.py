from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class ROIAnalyzer:
    """V225: ROI analyzer."""
    def analyze(self, effort_hours: float, expected_gain: float, risk_cost: float = 0.0) -> ControlArtifact:
        roi = round((expected_gain - risk_cost) / max(1.0, effort_hours), 4)
        status = PlaneStatus.READY if roi >= 0.2 else PlaneStatus.WARN
        return ControlArtifact(new_id("roi"), "roi_analysis", "roi", status, min(1.0, max(0.0, roi)), {"effort_hours": effort_hours, "expected_gain": expected_gain, "risk_cost": risk_cost, "roi": roi})
