from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from world_interface.universal_world_resolver_v4 import UniversalWorldResolverV4, CapabilityEndpoint
w = UniversalWorldResolverV4()
w.register(CapabilityEndpoint("device_alarm", "device", "trusted", side_effect=True, device_side_effect=True))
r = w.resolve("device_alarm")
assert r["status"] == "resolved"
assert "global_device_serial" in r["controls"]
print("v31_0_world_resolver_smoke: pass")
