from __future__ import annotations
from .schemas import GoalContract, WorldCapability, CapabilityGap

class CapabilityExpansionKernel:
    """Safe capability self-expansion loop.

    Detect gaps, propose sandboxed expansion, do not auto-install unknown code.
    This is the final AI-shape behavior: missing capability is not ignored; it
    becomes a controlled plan with sandbox, tests, canary, approval, and rollback.
    """

    def analyze(self, contract: GoalContract, capabilities: list[WorldCapability]) -> list[CapabilityGap]:
        available_names = {c.name for c in capabilities if c.available}
        needs = []
        raw = contract.raw_input

        if any(x in raw for x in ["视频", "图片", "logo", "海报"]):
            needs.append("media_generation")
        if any(x in raw for x in ["邮件", "日程", "客户"]):
            needs.append("external_connector")
        if any(x in raw for x in ["最终", "AI形态", "自治", "自动执行"]):
            needs.append("ai_shape_core")
        if any(x in raw for x in ["压缩包", "覆盖", "版本"]):
            needs.append("release_packager")
        if any(x in raw for x in ["缺技能", "缺能力", "新能力", "沙箱", "评测", "灰度", "上线", "安装技能", "扩展能力"]):
            needs.append("dynamic_capability_expansion")

        mapping = {
            "ai_shape_core": "ai_shape_core",
            "release_packager": "release_hardening",
            "external_connector": "action_bridge",
            "media_generation": "action_bridge",
            # Dynamic capability expansion is always treated as a managed gap,
            # even when platform primitives exist, because the concrete target
            # capability is unknown until sandbox evaluation.
            "dynamic_capability_expansion": None,
        }

        gaps = []
        for need in list(dict.fromkeys(needs)):
            mapped = mapping.get(need, need)
            if need == "dynamic_capability_expansion":
                available = False
            else:
                available = mapped in available_names
            gaps.append(CapabilityGap(
                capability=need,
                needed=True,
                available=available,
                safe_expansion_plan=[
                    "detect exact missing capability",
                    "search trusted internal registry first",
                    "create isolated sandbox/canary workspace",
                    "run static scan, contract tests, golden-path tests",
                    "compare result against baseline quality/cost/safety",
                    "promote behind feature flag only after approval",
                    "record rollback plan and evidence bundle",
                ],
                approval_required=(not available) or need == "dynamic_capability_expansion",
            ))
        return gaps
