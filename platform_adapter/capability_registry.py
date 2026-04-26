"""V11.3 Capability Registry and Device Profile."""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional
from platform_adapter.runtime_state_store import connect, init_runtime_tables, _now_ms
STATUS_PRIORITY={"connected":3,"probe_only":2,"offline":1,"unknown":0}
def _close(conn):
    try: conn.commit()
    finally: conn.close()
def init_capability_tables(db_path: Optional[Path]=None) -> None:
    init_runtime_tables(db_path); conn=connect(db_path)
    try: conn.executescript("""CREATE TABLE IF NOT EXISTS runtime_capabilities (capability TEXT PRIMARY KEY,adapter_name TEXT,status TEXT NOT NULL,supports_side_effect INTEGER DEFAULT 0,last_probe_ms INTEGER DEFAULT 0,stale_after_ms INTEGER DEFAULT 300000,detail_json TEXT,updated_at_ms INTEGER NOT NULL);""")
    finally: _close(conn)
@dataclass
class CapabilityState:
    capability: str; adapter_name: Optional[str]; status: str; supports_side_effect: bool; last_probe_ms: int; stale_after_ms: int; detail: Dict[str, Any]; stale: bool=False
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
def _detail(value):
    if not value: return {}
    try:
        parsed=json.loads(value); return parsed if isinstance(parsed,dict) else {"value":parsed}
    except Exception: return {"raw":value}
def upsert_capability(capability,*,adapter_name=None,status="unknown",supports_side_effect=False,stale_after_ms=300000,detail=None,db_path=None):
    init_capability_tables(db_path); now=_now_ms(); conn=connect(db_path)
    try:
        conn.execute("INSERT INTO runtime_capabilities(capability,adapter_name,status,supports_side_effect,last_probe_ms,stale_after_ms,detail_json,updated_at_ms) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(capability) DO UPDATE SET adapter_name=excluded.adapter_name,status=excluded.status,supports_side_effect=excluded.supports_side_effect,last_probe_ms=excluded.last_probe_ms,stale_after_ms=excluded.stale_after_ms,detail_json=excluded.detail_json,updated_at_ms=excluded.updated_at_ms", (capability,adapter_name,status,1 if supports_side_effect else 0,now,stale_after_ms,json.dumps(detail or {},ensure_ascii=False,sort_keys=True,default=str),now))
    finally: _close(conn)
    return get_capability(capability, db_path=db_path)
def get_capability(capability,*,db_path=None):
    init_capability_tables(db_path); now=_now_ms(); conn=connect(db_path)
    try: row=conn.execute("SELECT * FROM runtime_capabilities WHERE capability=?", (capability,)).fetchone()
    finally: conn.close()
    if not row: return CapabilityState(capability,None,"unknown",False,0,300000,{},True)
    stale=bool(row["last_probe_ms"] and (now-int(row["last_probe_ms"])>int(row["stale_after_ms"] or 300000))); status=row["status"]
    if stale and status=="connected": status="probe_only"
    return CapabilityState(row["capability"],row["adapter_name"],status,bool(row["supports_side_effect"]),int(row["last_probe_ms"] or 0),int(row["stale_after_ms"] or 300000),_detail(row["detail_json"]),stale)
def register_default_capabilities(db_path=None):
    defaults=[("MESSAGE_SENDING","xiaoyi_adapter","probe_only",True),("TASK_SCHEDULING","scheduler_adapter","probe_only",True),("NOTIFICATION","notification_adapter","probe_only",True),("calendar","calendar_adapter","probe_only",True),("file_write","local_fs","connected",True),("search","local_search","connected",False),("memory_read","memory_context","connected",False)]
    return [upsert_capability(c,adapter_name=a,status=s,supports_side_effect=se,db_path=db_path).to_dict() for c,a,s,se in defaults]
def device_profile(db_path=None):
    init_capability_tables(db_path); conn=connect(db_path)
    try: rows=conn.execute("SELECT * FROM runtime_capabilities ORDER BY capability").fetchall()
    finally: conn.close()
    states=[get_capability(r["capability"],db_path=db_path).to_dict() for r in rows]; best=max((STATUS_PRIORITY.get(s["status"],0) for s in states), default=0)
    adapter_status="connected" if best>=3 else "probe_only" if best==2 else "offline" if best==1 else "unknown"
    return {"adapter_status":adapter_status,"capabilities":states,"generated_at_ms":_now_ms()}
def mark_probe_result(capability,*,ok,direct=False,detail=None,db_path=None):
    status="connected" if ok and direct else "probe_only" if ok else "offline"; existing=get_capability(capability,db_path=db_path)
    return upsert_capability(capability,adapter_name=existing.adapter_name,status=status,supports_side_effect=existing.supports_side_effect,detail=detail or {},db_path=db_path)
