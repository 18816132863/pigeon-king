class HabitTwin:
    def extract(self, events: list[dict]) -> dict:
        return {
            "iteration_speed": "fast" if len(events) >= 3 else "normal",
            "handoff_preference": "zip_and_command",
            "validation_preference": "direct_check_then_package",
        }
