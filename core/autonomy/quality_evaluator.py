from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from .schemas import QualityReport, new_id
from .storage import JsonStore


class QualityEvaluator:
    """V93: result quality evaluator."""

    def __init__(self, root: str | Path = ".autonomy_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "quality_reports.json")

    def evaluate(self, run_id: str, goal: str, result: Dict, risk_blocked: bool = False) -> QualityReport:
        issues: List[str] = []

        completeness = 0.9 if result.get("has_plan") and result.get("has_next_action") else 0.55
        usefulness = 0.9 if result.get("actionable") else 0.6
        efficiency = 0.85 if result.get("steps", 0) <= 10 else 0.65
        safety = 0.95 if not risk_blocked else 0.72

        if not result.get("has_plan"):
            issues.append("missing_plan")
        if not result.get("has_next_action"):
            issues.append("missing_next_action")
        if risk_blocked:
            issues.append("waiting_for_approval")

        final_score = round((completeness * 0.35 + usefulness * 0.25 + safety * 0.25 + efficiency * 0.15), 4)
        report = QualityReport(
            id=new_id("quality"),
            run_id=run_id,
            goal=goal,
            completeness=completeness,
            safety=safety,
            usefulness=usefulness,
            efficiency=efficiency,
            final_score=final_score,
            passed=final_score >= 0.75,
            issues=issues,
        )
        self.store.append(self._to_dict(report))
        return report

    def latest(self) -> Optional[QualityReport]:
        data = self.store.read([])
        if not data:
            return None
        return self._from_dict(data[-1])

    def _to_dict(self, q: QualityReport) -> Dict:
        return {
            "id": q.id,
            "run_id": q.run_id,
            "goal": q.goal,
            "completeness": q.completeness,
            "safety": q.safety,
            "usefulness": q.usefulness,
            "efficiency": q.efficiency,
            "final_score": q.final_score,
            "passed": q.passed,
            "issues": q.issues,
        }

    def _from_dict(self, item: Dict) -> QualityReport:
        return QualityReport(
            id=item["id"],
            run_id=item["run_id"],
            goal=item["goal"],
            completeness=float(item.get("completeness", 0.0)),
            safety=float(item.get("safety", 0.0)),
            usefulness=float(item.get("usefulness", 0.0)),
            efficiency=float(item.get("efficiency", 0.0)),
            final_score=float(item.get("final_score", 0.0)),
            passed=bool(item.get("passed", False)),
            issues=list(item.get("issues", [])),
        )
