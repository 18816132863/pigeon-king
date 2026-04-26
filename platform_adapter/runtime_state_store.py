"""V11.1 Runtime State Store: durable action ledger, idempotency reservation, and delivery queue."""
from __future__ import annotations
import hashlib, json, sqlite3, time
from contextlib import closing
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "tasks.db"
TERMINAL_STATES = {"completed", "failed", "cancelled", "blocked"}
ACTIVE_STATES = {"planned", "requires_confirmation", "queued", "running", "hold_for_result_check"}
def _now_ms() -> int: return int(time.time() * 1000)
def _json(value: Any) -> str: return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)
def _load(value: Optional[str]) -> Dict[str, Any]:
    if not value: return {}
    try:
        parsed=json.loads(value); return parsed if isinstance(parsed, dict) else {"value": parsed}
    except Exception: return {"raw": value}
def canonical_hash(payload: Dict[str, Any]) -> str: return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()[:20]
def make_action_id(capability: str, op_name: str, payload: Optional[Dict[str, Any]]=None) -> str: return f"act:{capability}:{op_name}:{canonical_hash(payload or {})}"
def make_idempotency_key(task_id: Optional[str], capability: str, op_name: str, payload: Optional[Dict[str, Any]]=None) -> str: return f"{task_id or 'global'}:{capability}:{op_name}:{canonical_hash(payload or {})}"
def connect(db_path: Optional[Path]=None) -> sqlite3.Connection:
    path=Path(db_path or DB_PATH); path.parent.mkdir(parents=True, exist_ok=True)
    conn=sqlite3.connect(str(path), isolation_level=None); conn.row_factory=sqlite3.Row; return conn
def init_runtime_tables(db_path: Optional[Path]=None) -> None:
    with closing(connect(db_path)) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS runtime_actions (
            action_id TEXT PRIMARY KEY, task_id TEXT, idempotency_key TEXT UNIQUE NOT NULL,
            capability TEXT NOT NULL, op_name TEXT NOT NULL, risk_level TEXT DEFAULT 'L1',
            state TEXT NOT NULL, payload_json TEXT, result_json TEXT, retry_count INTEGER DEFAULT 0,
            last_error TEXT, locked_until_ms INTEGER DEFAULT 0, confirmation_token TEXT,
            created_at_ms INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS runtime_action_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT, action_id TEXT NOT NULL, from_state TEXT,
            to_state TEXT NOT NULL, reason TEXT, event_json TEXT, created_at_ms INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS runtime_delivery_queue (
            queue_id INTEGER PRIMARY KEY AUTOINCREMENT, action_id TEXT NOT NULL, delivery_mode TEXT NOT NULL,
            state TEXT NOT NULL, not_before_ms INTEGER DEFAULT 0, attempts INTEGER DEFAULT 0, last_error TEXT,
            created_at_ms INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS runtime_idempotency_reservations (
            idempotency_key TEXT PRIMARY KEY, action_id TEXT NOT NULL, state TEXT NOT NULL,
            expires_at_ms INTEGER NOT NULL, created_at_ms INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL);
        """)
def _insert_event(conn, action_id, from_state, to_state, reason="", event=None):
    conn.execute("INSERT INTO runtime_action_events(action_id,from_state,to_state,reason,event_json,created_at_ms) VALUES (?,?,?,?,?,?)", (action_id, from_state, to_state, reason, _json(event or {}), _now_ms()))
@dataclass
class RuntimeAction:
    action_id: str; idempotency_key: str; capability: str; op_name: str; state: str
    task_id: Optional[str]=None; risk_level: str="L1"; payload: Optional[Dict[str, Any]]=None
    result: Optional[Dict[str, Any]]=None; retry_count: int=0; last_error: Optional[str]=None
    confirmation_token: Optional[str]=None; created_at_ms: int=0; updated_at_ms: int=0; duplicated: bool=False
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
def _row_to_action(row, duplicated=False) -> RuntimeAction:
    return RuntimeAction(row["action_id"], row["idempotency_key"], row["capability"], row["op_name"], row["state"], row["task_id"], row["risk_level"], _load(row["payload_json"]), _load(row["result_json"]), int(row["retry_count"] or 0), row["last_error"], row["confirmation_token"], int(row["created_at_ms"]), int(row["updated_at_ms"]), duplicated)
def register_action(*, capability, op_name, payload=None, task_id=None, risk_level="L1", idempotency_key=None, initial_state="planned", db_path=None) -> RuntimeAction:
    init_runtime_tables(db_path); payload=payload or {}; idempotency_key=idempotency_key or make_idempotency_key(task_id, capability, op_name, payload)
    action_id=make_action_id(capability, op_name, {"task_id":task_id,"idempotency_key":idempotency_key,"payload":payload}); now=_now_ms()
    with closing(connect(db_path)) as conn:
        existing=conn.execute("SELECT * FROM runtime_actions WHERE idempotency_key=?", (idempotency_key,)).fetchone()
        if existing: return _row_to_action(existing, True)
        conn.execute("INSERT INTO runtime_actions(action_id,task_id,idempotency_key,capability,op_name,risk_level,state,payload_json,created_at_ms,updated_at_ms) VALUES (?,?,?,?,?,?,?,?,?,?)", (action_id,task_id,idempotency_key,capability,op_name,risk_level,initial_state,_json(payload),now,now))
        _insert_event(conn, action_id, None, initial_state, "registered", {"risk_level":risk_level})
        return _row_to_action(conn.execute("SELECT * FROM runtime_actions WHERE action_id=?", (action_id,)).fetchone())
def get_action(action_id=None, *, idempotency_key=None, db_path=None):
    init_runtime_tables(db_path)
    with closing(connect(db_path)) as conn:
        row=conn.execute("SELECT * FROM runtime_actions WHERE idempotency_key=?" if idempotency_key else "SELECT * FROM runtime_actions WHERE action_id=?", (idempotency_key or action_id,)).fetchone()
        return _row_to_action(row) if row else None
def transition_action(action_id, to_state, *, reason="", result=None, error=None, db_path=None) -> RuntimeAction:
    init_runtime_tables(db_path); now=_now_ms()
    with closing(connect(db_path)) as conn:
        row=conn.execute("SELECT * FROM runtime_actions WHERE action_id=?", (action_id,)).fetchone()
        if not row: raise KeyError(f"unknown action_id: {action_id}")
        conn.execute("UPDATE runtime_actions SET state=?, result_json=COALESCE(?, result_json), last_error=?, updated_at_ms=? WHERE action_id=?", (to_state, _json(result) if result is not None else None, error, now, action_id))
        _insert_event(conn, action_id, row["state"], to_state, reason, {"result":result or {}, "error":error})
        return _row_to_action(conn.execute("SELECT * FROM runtime_actions WHERE action_id=?", (action_id,)).fetchone())
def acquire_reservation(idempotency_key, action_id, *, ttl_ms=300000, db_path=None) -> bool:
    init_runtime_tables(db_path); now=_now_ms(); expires=now+max(ttl_ms,1000)
    with closing(connect(db_path)) as conn:
        row=conn.execute("SELECT * FROM runtime_idempotency_reservations WHERE idempotency_key=?", (idempotency_key,)).fetchone()
        if row and int(row["expires_at_ms"])>now and row["state"]=="reserved": return False
        conn.execute("INSERT INTO runtime_idempotency_reservations(idempotency_key,action_id,state,expires_at_ms,created_at_ms,updated_at_ms) VALUES (?,?,'reserved',?,?,?) ON CONFLICT(idempotency_key) DO UPDATE SET action_id=excluded.action_id,state='reserved',expires_at_ms=excluded.expires_at_ms,updated_at_ms=excluded.updated_at_ms", (idempotency_key,action_id,expires,now,now)); return True
def release_reservation(idempotency_key, *, final_state="released", db_path=None) -> None:
    init_runtime_tables(db_path)
    with closing(connect(db_path)) as conn: conn.execute("UPDATE runtime_idempotency_reservations SET state=?, updated_at_ms=? WHERE idempotency_key=?", (final_state,_now_ms(),idempotency_key))
def enqueue_action(action_id, *, delivery_mode="queued_for_delivery", not_before_ms=0, db_path=None) -> int:
    init_runtime_tables(db_path); now=_now_ms()
    with closing(connect(db_path)) as conn:
        conn.execute("UPDATE runtime_actions SET state='queued', updated_at_ms=? WHERE action_id=?", (now,action_id)); _insert_event(conn, action_id, None, "queued", f"delivery_mode={delivery_mode}", {"not_before_ms":not_before_ms})
        cur=conn.execute("INSERT INTO runtime_delivery_queue(action_id,delivery_mode,state,not_before_ms,attempts,created_at_ms,updated_at_ms) VALUES (?,?,'pending',?,0,?,?)", (action_id,delivery_mode,not_before_ms,now,now)); return int(cur.lastrowid)
def list_actions(*, state=None, limit=50, db_path=None):
    init_runtime_tables(db_path)
    with closing(connect(db_path)) as conn:
        rows=conn.execute("SELECT * FROM runtime_actions WHERE state=? ORDER BY updated_at_ms DESC LIMIT ?" if state else "SELECT * FROM runtime_actions ORDER BY updated_at_ms DESC LIMIT ?", (state,limit) if state else (limit,)).fetchall()
        return [_row_to_action(r).to_dict() for r in rows]
def summarize_runtime(db_path=None) -> Dict[str, Any]:
    init_runtime_tables(db_path)
    with closing(connect(db_path)) as conn:
        ac={r["state"]:r["n"] for r in conn.execute("SELECT state,COUNT(*) n FROM runtime_actions GROUP BY state").fetchall()}
        qc={r["state"]:r["n"] for r in conn.execute("SELECT state,COUNT(*) n FROM runtime_delivery_queue GROUP BY state").fetchall()}
        return {"db_path":str(Path(db_path or DB_PATH)),"action_counts":ac,"queue_counts":qc,"active_count":sum(ac.get(s,0) for s in ACTIVE_STATES),"terminal_count":sum(ac.get(s,0) for s in TERMINAL_STATES),"generated_at_ms":_now_ms()}
