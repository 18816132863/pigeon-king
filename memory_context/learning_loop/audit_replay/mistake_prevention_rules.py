class MistakePreventionRules:
    def derive(self, failures: list[dict]) -> dict:
        rules = []
        for f in failures:
            if "permission" in str(f):
                rules.append("precheck_permission_before_execution")
            if "timeout" in str(f):
                rules.append("probe_adapter_before_route")
        return {"status": "rules_ready", "rules": sorted(set(rules))}
