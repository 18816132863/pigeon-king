class IncidentManager:
    def open_incident(self, title: str, severity: str = "warning") -> dict:
        return {
            "status": "incident_opened",
            "title": title,
            "severity": severity,
            "auto_recovery_allowed": severity not in {"critical", "security"},
            "requires_user_notice": severity in {"critical", "security"},
        }
