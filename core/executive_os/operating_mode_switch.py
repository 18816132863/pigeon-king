class OperatingModeSwitch:
    MODES = {
        "safe": {"auto_execute": False, "auto_search": True, "auto_extend": False},
        "bounded_auto": {"auto_execute": True, "auto_search": True, "auto_extend": "sandbox"},
        "real_world": {"auto_execute": "authorized_only", "auto_search": True, "auto_extend": "approval_required"},
    }

    def select(self, intent: dict, reality: dict) -> dict:
        if intent.get("needs_external_connection"):
            mode = "real_world"
        elif intent.get("needs_self_extension"):
            mode = "bounded_auto"
        else:
            mode = "bounded_auto"
        if reality.get("uncertainty", {}).get("uncertainty_level") == "high":
            mode = "safe"
        return {"status": "selected", "mode": mode, "policy": self.MODES[mode]}
