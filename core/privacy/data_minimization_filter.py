class DataMinimizationFilter:
    def minimize(self, payload: dict, allowed_keys: list[str]) -> dict:
        return {k: v for k, v in payload.items() if k in allowed_keys}
