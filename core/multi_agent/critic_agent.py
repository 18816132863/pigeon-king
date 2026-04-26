class CriticAgent:
    """Find contradictions, missing info and unsafe assumptions before execution."""

    def critique(self, plan: dict) -> dict:
        issues = []
        text = str(plan)
        if "绕过确认" in text:
            issues.append("attempt_to_bypass_confirmation")
        if "未知代码直接安装" in text:
            issues.append("unsafe_direct_install")
        if not plan:
            issues.append("empty_plan")
        return {"status": "pass" if not issues else "review_required", "issues": issues}
