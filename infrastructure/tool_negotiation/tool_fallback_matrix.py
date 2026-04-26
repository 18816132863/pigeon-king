class ToolFallbackMatrix:
    def build(self, required_capability: str, tools: list[dict]) -> dict:
        primary = next((t for t in tools if required_capability in t.get("capabilities", [])), None)
        fallbacks = [t for t in tools if t is not primary and required_capability in t.get("capabilities", [])]
        return {
            "status": "fallback_matrix_ready",
            "required_capability": required_capability,
            "primary": primary,
            "fallbacks": fallbacks,
            "missing": primary is None,
        }
