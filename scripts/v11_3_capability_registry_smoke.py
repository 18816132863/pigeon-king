#!/usr/bin/env python3
from pathlib import Path
import sys, os, tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.capability_registry import register_default_capabilities, mark_probe_result, device_profile
def main():
    db=Path(tempfile.gettempdir())/"pigeon_v11_3_smoke.db"
    if db.exists(): db.unlink()
    register_default_capabilities(db_path=db)
    state=mark_probe_result("MESSAGE_SENDING",ok=True,direct=False,detail={"bridge":"probe-only"},db_path=db)
    assert state.status=="probe_only"
    prof=device_profile(db_path=db)
    assert "capabilities" in prof
    os.write(1, b"v11_3_capability_registry_smoke OK\n")
if __name__=="__main__":
    main(); os._exit(0)
