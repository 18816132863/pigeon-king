class ScopeRedactionPolicy:
    SENSITIVE_KEYS = {"api_key", "token", "password", "secret", "phone", "id_card"}

    def redact(self, payload: dict) -> dict:
        return {k: ("[REDACTED]" if k in self.SENSITIVE_KEYS else v) for k, v in payload.items()}
