from __future__ import annotations

from pathlib import Path
from typing import List
import os
from .schemas import ConfigContract, CheckStatus, new_id
from .storage import JsonStore


class ConfigContractManager:
    """V128: required/optional runtime configuration contract."""

    DEFAULT_REQUIRED: List[str] = []
    DEFAULT_OPTIONAL: List[str] = [
        "OPENAI_API_KEY",
        "DEEPSEEK_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "DASHSCOPE_API_KEY",
        "MOONSHOT_API_KEY",
        "ZHIPU_API_KEY",
    ]

    def __init__(self, root: str | Path = ".release_hardening_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "config_contract.json")

    def evaluate(self, required_env: List[str] | None = None, optional_env: List[str] | None = None) -> ConfigContract:
        required = required_env if required_env is not None else self.DEFAULT_REQUIRED
        optional = optional_env if optional_env is not None else self.DEFAULT_OPTIONAL
        present = [x for x in required if os.environ.get(x)]
        missing = [x for x in required if not os.environ.get(x)]
        status = CheckStatus.FAIL if missing else CheckStatus.PASS
        notes = []
        optional_present = [x for x in optional if os.environ.get(x)]
        notes.append(f"optional_present:{len(optional_present)}/{len(optional)}")
        contract = ConfigContract(
            id=new_id("config"),
            required_env=required,
            optional_env=optional,
            present_required=present,
            missing_required=missing,
            status=status,
            notes=notes,
        )
        self.store.write(contract.__dict__ | {"status": contract.status.value})
        return contract
