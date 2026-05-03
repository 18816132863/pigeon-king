from __future__ import annotations

from importlib.util import find_spec


class LegacyModuleAdapter:
    """Adapts V85-V316 modules into AI_SHAPE_CORE availability checks."""

    REQUIRED_LAYERS = {
        "V85_model_router": "core.llm",
        "V86_personal_agent": "core.personal_agent",
        "V87_V96_autonomy": "core.autonomy",
        "V97_V106_operating_agent": "core.operating_agent",
        "V107_V116_self_evolution": "core.self_evolution_ops",
        "V117_V126_operating_spine": "core.operating_spine",
        "V127_V136_release_hardening": "core.release_hardening",
        "V137_V146_runtime_activation": "core.runtime_activation",
        "V147_V156_action_bridge": "core.action_bridge",
        "V157_V166_personalization": "core.personalization",
        "V167_V196_operations_intelligence": "core.operations_intelligence",
        "V197_V226_control_plane": "core.production_control_plane",
        "V227_V256_runtime_fabric": "core.autonomous_runtime_fabric",
        "V257_V316_meta_platform": "core.meta_autonomy_platform",
        "FINAL_ai_shape_core": "core.ai_shape_core",
    }

    def inspect(self) -> dict:
        layers = {name: find_spec(module) is not None for name, module in self.REQUIRED_LAYERS.items()}
        present = sum(1 for v in layers.values() if v)
        return {
            "layers": layers,
            "present": present,
            "total": len(layers),
            "coverage": round(present / max(1, len(layers)), 4),
            "missing": [k for k, v in layers.items() if not v],
        }
