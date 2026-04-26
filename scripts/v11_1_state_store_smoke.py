#!/usr/bin/env python3
from pathlib import Path
import sys, os, tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.runtime_state_store import register_action, acquire_reservation, enqueue_action, summarize_runtime
def main():
    db=Path(tempfile.gettempdir())/"pigeon_v11_1_smoke.db"
    if db.exists(): db.unlink()
    a1=register_action(capability="MESSAGE_SENDING",op_name="send_message",payload={"to":"demo","text":"hi"},task_id="smoke",risk_level="L3",db_path=db)
    a2=register_action(capability="MESSAGE_SENDING",op_name="send_message",payload={"to":"demo","text":"hi"},task_id="smoke",risk_level="L3",db_path=db)
    assert a2.duplicated is True
    assert acquire_reservation(a1.idempotency_key,a1.action_id,db_path=db) is True
    assert acquire_reservation(a1.idempotency_key,a1.action_id,db_path=db) is False
    assert enqueue_action(a1.action_id,db_path=db)>=1
    print({"ok":True,"action_id":a1.action_id,"duplicated":a2.duplicated,"summary":summarize_runtime(db_path=db)})
if __name__=="__main__":
    main(); os._exit(0)
