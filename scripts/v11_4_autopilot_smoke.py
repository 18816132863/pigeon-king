#!/usr/bin/env python3
from pathlib import Path
import sys, os, tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from governance.policy.execution_autopilot import plan_runtime_action
def main():
    db=Path(tempfile.gettempdir())/"pigeon_v11_4_smoke.db"
    if db.exists(): db.unlink()
    first=plan_runtime_action(capability="MESSAGE_SENDING",op_name="send_message",payload={"to":"demo","text":"hi"},task_id="smoke",risk_level="L3",db_path=db)
    assert first["status"]=="requires_confirmation"
    token=first["confirmation"]["confirmation_token"]
    second=plan_runtime_action(capability="MESSAGE_SENDING",op_name="send_message",payload={"to":"demo","text":"hi"},task_id="smoke",risk_level="L3",provided_confirmation_token=token,db_path=db)
    assert second["status"] in {"queued","allowed"}
    uncertain=plan_runtime_action(capability="MESSAGE_SENDING",op_name="send_message",payload={"to":"demo","text":"hi2"},task_id="smoke2",risk_level="L3",result_uncertain=True,db_path=db)
    assert uncertain["status"]=="hold_for_result_check"
    print({"ok":True,"first":first["status"],"second":second["status"],"uncertain":uncertain["status"]})
if __name__=="__main__":
    main(); os._exit(0)
