#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from platform_adapter.world_interface_resolver_v2 import WorldInterface, WorldInterfaceResolverV2

resolver = WorldInterfaceResolverV2()
resolver.register(WorldInterface("device_alarm", "device", "builtin", ["alarm.modify", "alarm.search"]))
resolver.register(WorldInterface("local_files", "local", "trusted", ["file.read"]))
assert resolver.has_capability("alarm.modify")
assert [i.name for i in resolver.resolve("file.read")] == ["local_files"]
print("v25_5_world_interface_resolver_smoke: pass")
