#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_kernel.layer_integrity_gate_v2 import LayerIntegrityGateV2

gate = LayerIntegrityGateV2()
ok = gate.check_manifest({"agent_kernel/personal_operating_loop_v2.py": "L3 Orchestration"})
bad = gate.check_manifest({"agent_kernel/personal_operating_loop_v2.py": "L7 Agent Kernel"})
assert ok.ok is True
assert bad.ok is False
print("v25_1_layer_integrity_gate_smoke: pass")
