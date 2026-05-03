from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import CapabilityContract, CapabilityContractStatus, new_id, to_dict
from .storage import JsonStore


class CapabilityContractRegistry:
    """V119: capability contract registry.

    It validates whether core modules expose the minimal methods required for
    orchestration without hard-coding implementation details.
    """

    DEFAULTS = [
        ("model_router", "core.llm", ["auto_route", "call"], "fast_low_cost"),
        ("personal_execution_agent", "core.personal_agent", ["PersonalExecutionAgent"], "manual_plan"),
        ("autonomy_kernel", "core.autonomy", ["run_autonomy_cycle", "init_autonomy_system"], "basic_autonomy"),
        ("operating_governance", "core.operating_agent", ["run_operating_cycle", "init_operating_agent"], "constitution_only"),
        ("self_evolution_ops", "core.self_evolution_ops", ["run_self_evolution_cycle", "init_self_evolution_ops"], "safe_static_ops"),
    ]

    def __init__(self, root: str | Path = ".operating_spine_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "capability_contracts.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.store.read([]):
            return
        data = []
        for name, provider, methods, fallback in self.DEFAULTS:
            data.append(to_dict(CapabilityContract(
                id=new_id("contract"),
                name=name,
                provider_module=provider,
                required_methods=methods,
                status=CapabilityContractStatus.MISSING,
                fallback=fallback,
            )))
        self.store.write(data)

    def validate_all(self) -> List[CapabilityContract]:
        results = []
        for item in self.store.read([]):
            contract = self._from_dict(item)
            missing = []
            try:
                module = __import__(contract.provider_module, fromlist=["*"])
                for method in contract.required_methods:
                    if not hasattr(module, method):
                        missing.append(method)
            except Exception:
                missing = list(contract.required_methods)

            if not missing:
                status = CapabilityContractStatus.ACTIVE
            elif contract.fallback:
                status = CapabilityContractStatus.DEGRADED
            else:
                status = CapabilityContractStatus.MISSING

            results.append(CapabilityContract(
                id=contract.id,
                name=contract.name,
                provider_module=contract.provider_module,
                required_methods=contract.required_methods,
                status=status,
                missing_methods=missing,
                fallback=contract.fallback,
            ))

        self.store.write([to_dict(x) for x in results])
        return results

    def active_count(self) -> int:
        return sum(1 for x in self.validate_all() if x.status == CapabilityContractStatus.ACTIVE)

    def _from_dict(self, item: Dict) -> CapabilityContract:
        return CapabilityContract(
            id=item["id"],
            name=item["name"],
            provider_module=item["provider_module"],
            required_methods=list(item.get("required_methods", [])),
            status=CapabilityContractStatus(item.get("status", CapabilityContractStatus.MISSING.value)),
            missing_methods=list(item.get("missing_methods", [])),
            fallback=item.get("fallback"),
        )
