from __future__ import annotations
from importlib.util import find_spec
from pathlib import Path
from typing import List
from .schemas import WorldCapability

class WorldInterface:
    """Unified world interface over legacy V85-V316 layers."""

    LAYERS = {
        "model_router": ("core.llm", "model routing and model API gateway"),
        "personal_execution_agent": ("core.personal_agent", "goal execution agent"),
        "autonomy_kernel": ("core.autonomy", "autonomy kernel"),
        "operating_agent": ("core.operating_agent", "constitution and operating governance"),
        "self_evolution_ops": ("core.self_evolution_ops", "self-evolution operations"),
        "operating_spine": ("core.operating_spine", "unified operating spine"),
        "release_hardening": ("core.release_hardening", "release and rollback hardening"),
        "runtime_activation": ("core.runtime_activation", "command/API/job activation"),
        "action_bridge": ("core.action_bridge", "safe real-world action bridge"),
        "personalization": ("core.personalization", "user preference and memory learning"),
        "operations_intelligence": ("core.operations_intelligence", "operations intelligence"),
        "production_control_plane": ("core.production_control_plane", "production control plane"),
        "autonomous_runtime_fabric": ("core.autonomous_runtime_fabric", "self-healing runtime fabric"),
        "meta_autonomy_platform": ("core.meta_autonomy_platform", "large-scale autonomy platform"),
        "ai_shape_core": ("core.ai_shape_core", "final unified AI-shape main chain"),
    }

    def capabilities(self) -> List[WorldCapability]:
        caps = []
        for name, (module, desc) in self.LAYERS.items():
            caps.append(WorldCapability(
                name=name,
                layer=module,
                available=find_spec(module) is not None,
                safe_default=True,
                description=desc,
            ))
        return caps

    def source_list(self, goal: str) -> list[str]:
        sources = ["user_input", "unified_memory", "constitution_rules", "world_capability_registry"]
        if any(x in goal for x in ["版本", "压缩包", "覆盖", "替换"]):
            sources += ["workspace_files", "merged_v85_v316_packages", "final_ai_shape_verifier"]
        if any(x in goal for x in ["邮件", "日程", "客户"]):
            sources += ["external_connectors_if_enabled"]
        return list(dict.fromkeys(sources))
