"""V12.1 local trace recorder."""
from __future__ import annotations
import json
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, List, Optional
from infrastructure.platform_adapter.runtime_state_store import connect, init_runtime_tables, _now_ms, _json

def init_trace_tables(db_path: Optional[Path]=None)->None:
    init_runtime_tables(db_path)
    with closing(connect(db_path)) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS runtime_trace_events(
            trace_id INTEGER PRIMARY KEY AUTOINCREMENT, correlation_id TEXT NOT NULL, action_id TEXT,
            stage TEXT NOT NULL, status TEXT NOT NULL, message TEXT, payload_json TEXT, created_at_ms INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_trace_corr ON runtime_trace_events(correlation_id, created_at_ms);
        CREATE INDEX IF NOT EXISTS idx_trace_action ON runtime_trace_events(action_id, created_at_ms);
        """)

def _load(s):
    if not s: return {}
    try:
        v=json.loads(s); return v if isinstance(v, dict) else {"value":v}
    except Exception: return {"raw":s}

def record_trace(*, stage:str, status:str, message:str='', payload:Optional[Dict[str,Any]]=None, action_id:Optional[str]=None, correlation_id:Optional[str]=None, db_path:Optional[Path]=None)->Dict[str,Any]:
    init_trace_tables(db_path); corr=correlation_id or action_id or 'runtime'; now=_now_ms()
    with closing(connect(db_path)) as conn:
        cur=conn.execute('INSERT INTO runtime_trace_events(correlation_id,action_id,stage,status,message,payload_json,created_at_ms) VALUES (?,?,?,?,?,?,?)',(corr,action_id,stage,status,message,_json(payload or {}),now))
        row=conn.execute('SELECT * FROM runtime_trace_events WHERE trace_id=?',(cur.lastrowid,)).fetchone()
    return {"trace_id":int(row['trace_id']),"correlation_id":row['correlation_id'],"action_id":row['action_id'],"stage":row['stage'],"status":row['status'],"message":row['message'] or '',"payload":_load(row['payload_json']),"created_at_ms":int(row['created_at_ms'])}

def get_traces(*, correlation_id:Optional[str]=None, action_id:Optional[str]=None, limit:int=100, db_path:Optional[Path]=None)->List[Dict[str,Any]]:
    init_trace_tables(db_path)
    with closing(connect(db_path)) as conn:
        if action_id:
            rows=conn.execute('SELECT * FROM runtime_trace_events WHERE action_id=? ORDER BY created_at_ms,trace_id LIMIT ?',(action_id,max(1,limit))).fetchall()
        elif correlation_id:
            rows=conn.execute('SELECT * FROM runtime_trace_events WHERE correlation_id=? ORDER BY created_at_ms,trace_id LIMIT ?',(correlation_id,max(1,limit))).fetchall()
        else:
            rows=conn.execute('SELECT * FROM runtime_trace_events ORDER BY created_at_ms DESC,trace_id DESC LIMIT ?',(max(1,limit),)).fetchall()
    return [{"trace_id":int(r['trace_id']),"correlation_id":r['correlation_id'],"action_id":r['action_id'],"stage":r['stage'],"status":r['status'],"message":r['message'] or '',"payload":_load(r['payload_json']),"created_at_ms":int(r['created_at_ms'])} for r in rows]

def build_trace_report(*, correlation_id:Optional[str]=None, action_id:Optional[str]=None, db_path:Optional[Path]=None)->Dict[str,Any]:
    traces=get_traces(correlation_id=correlation_id, action_id=action_id, limit=500, db_path=db_path); by_status={}; by_stage={}
    for t in traces:
        by_status[t['status']]=by_status.get(t['status'],0)+1; by_stage[t['stage']]=by_stage.get(t['stage'],0)+1
    return {"trace_count":len(traces),"by_status":by_status,"by_stage":by_stage,"events":traces,"generated_at_ms":_now_ms()}
