from __future__ import annotations

from .schemas import DiagnosticReport, DiagnosticStatus, StateInspectionReport, CompatibilityReport, new_id


class DiagnosticEngine:
    """V142: combine checks into a diagnostic report."""

    def build(self, inspection: StateInspectionReport, compatibility: CompatibilityReport) -> DiagnosticReport:
        checks = {
            "inspection": inspection.status,
            "compatibility": DiagnosticStatus.PASS if compatibility.status.value == "compatible" else DiagnosticStatus.WARN,
            "cache": DiagnosticStatus.PASS if inspection.cache_count == 0 else DiagnosticStatus.WARN,
        }
        fail = sum(1 for v in checks.values() if v == DiagnosticStatus.FAIL)
        warn = sum(1 for v in checks.values() if v == DiagnosticStatus.WARN)
        score = round((len(checks) - fail - 0.5 * warn) / len(checks), 4)
        if fail:
            status = DiagnosticStatus.FAIL
        elif warn:
            status = DiagnosticStatus.WARN
        else:
            status = DiagnosticStatus.PASS
        recs = []
        if inspection.cache_count:
            recs.append("clean __pycache__ before final packaging")
        if compatibility.missing_layers:
            recs.append("install missing optional layers or rely on compatibility fallback")
        return DiagnosticReport(id=new_id("diag"), checks=checks, score=score, status=status, recommendations=recs)
