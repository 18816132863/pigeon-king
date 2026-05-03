from __future__ import annotations
import json, os, time
from pathlib import Path
from dataclasses import is_dataclass, asdict
from enum import Enum
ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
STATE = ROOT / '.v107_state'

def safe_jsonable(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)): return obj
    if isinstance(obj, Enum): return obj.value
    if isinstance(obj, Path): return str(obj)
    if is_dataclass(obj): return safe_jsonable(asdict(obj))
    if isinstance(obj, dict): return {str(k): safe_jsonable(v) for k,v in obj.items()}
    if isinstance(obj, (list, tuple, set)): return [safe_jsonable(x) for x in obj]
    if hasattr(obj, 'model_dump'):
        try: return safe_jsonable(obj.model_dump())
        except Exception: pass
    if hasattr(obj, 'dict'):
        try: return safe_jsonable(obj.dict())
        except Exception: pass
    if hasattr(obj, '__dict__'):
        try: return safe_jsonable(vars(obj))
        except Exception: pass
    return str(obj)

def write_json(path, payload):
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(safe_jsonable(payload), ensure_ascii=False, indent=2), encoding='utf-8')

def read_json(path, default=None):
    p=Path(path)
    if not p.exists(): return default
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default

def env_summary():
    return {
        'offline_mode': os.environ.get('OFFLINE_MODE') == 'true',
        'no_external_api': os.environ.get('NO_EXTERNAL_API') == 'true',
        'no_real_send': os.environ.get('NO_REAL_SEND') == 'true',
        'no_real_payment': os.environ.get('NO_REAL_PAYMENT') == 'true',
        'no_real_device': os.environ.get('NO_REAL_DEVICE') == 'true',
        'disable_llm_api': os.environ.get('DISABLE_LLM_API') == 'true',
    }

class UnifiedObservabilityLedger:
    def __init__(self, root: Path | None = None):
        self.root=root or ROOT; self.state=self.root/'.v107_state'; self.ledger=self.state/'unified_observability_ledger.jsonl'; self.state.mkdir(parents=True, exist_ok=True)
    def record_event(self, event_type: str, payload: dict | None = None):
        entry={'ts':time.time(),'event_type':event_type,'payload':payload or {},'env':env_summary()}
        with self.ledger.open('a',encoding='utf-8') as f: f.write(json.dumps(safe_jsonable(entry),ensure_ascii=False)+'\n')
        return entry
    def record_gate(self, gate_name: str, status: str, payload: dict | None = None): return self.record_event('gate', {'gate_name':gate_name,'status':status,**(payload or {})})
    def current_release_status(self): return read_json(self.root/'reports'/'CURRENT_RELEASE_INDEX.json', {'status':'unknown','reason':'missing'})
    def status(self): return {'ready': True, 'ledger_path': str(self.ledger), 'events_written': self.ledger.exists()}

def record_event(event_type: str, payload: dict | None = None): return UnifiedObservabilityLedger().record_event(event_type, payload)
def record_gate(gate_name: str, status: str, payload: dict | None = None): return UnifiedObservabilityLedger().record_gate(gate_name,status,payload)
