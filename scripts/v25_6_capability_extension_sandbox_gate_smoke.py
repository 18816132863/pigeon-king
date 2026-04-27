#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from infrastructure.capability_extension_sandbox_gate_v2 import CapabilityExtensionSandboxGateV2, ExtensionCandidate

gate = CapabilityExtensionSandboxGateV2()
safe = ExtensionCandidate(
    name="trusted_calendar_connector",
    source="trusted_connector_catalog",
    capability_gap="calendar.search",
    install_mode="no_code_connector",
    has_hash=False,
    test_plan=["smoke"],
    rollback_plan=["disable_connector"],
)
bad = ExtensionCandidate(
    name="random_pkg",
    source="internet_unknown",
    capability_gap="unknown",
    install_mode="global_pip",
    has_hash=False,
    test_plan=[],
    rollback_plan=[],
)
assert gate.evaluate(safe).status == "promote_candidate"
assert gate.evaluate(bad).status == "quarantine"
print("v25_6_capability_extension_sandbox_gate_smoke: pass")
