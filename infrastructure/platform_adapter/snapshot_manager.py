"""V12.3 local SQLite snapshot manager."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path
from typing import Dict, List, Optional
from infrastructure.platform_adapter.runtime_state_store import DB_PATH, init_runtime_tables, _now_ms

def _sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def create_snapshot(*, db_path:Optional[Path]=None, snapshot_dir:Optional[Path]=None, label:str='manual')->Dict:
    db=Path(db_path or DB_PATH); init_runtime_tables(db); out=Path(snapshot_dir or db.parent/'snapshots'); out.mkdir(parents=True, exist_ok=True)
    safe=''.join(c if c.isalnum() or c in '-_' else '_' for c in label)[:80] or 'snapshot'; now=_now_ms(); snap=out/f'{now}_{safe}.sqlite3'; shutil.copy2(db,snap)
    meta={'label':label,'db_path':str(db),'snapshot_path':str(snap),'sha256':_sha256(snap),'bytes':snap.stat().st_size,'created_at_ms':now}; snap.with_suffix(snap.suffix+'.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8'); return meta

def list_snapshots(*, snapshot_dir:Path, limit:int=20)->List[Dict]:
    data=[]
    for m in sorted(Path(snapshot_dir).glob('*.sqlite3.json'), reverse=True)[:max(1,limit)]:
        try: data.append(json.loads(m.read_text(encoding='utf-8')))
        except Exception: data.append({'snapshot_path':str(m.with_suffix('')),'meta_error':True})
    return data

def verify_snapshot(snapshot_path:Path, *, expected_sha256:Optional[str]=None)->Dict:
    p=Path(snapshot_path)
    if not p.exists(): return {'ok':False,'reason':'missing_snapshot','snapshot_path':str(p)}
    d=_sha256(p); return {'ok':expected_sha256 in {None,d},'snapshot_path':str(p),'sha256':d,'bytes':p.stat().st_size,'reason':'ok' if expected_sha256 in {None,d} else 'sha256_mismatch'}

def restore_snapshot(*, snapshot_path:Path, target_db_path:Optional[Path]=None, expected_sha256:Optional[str]=None)->Dict:
    v=verify_snapshot(snapshot_path, expected_sha256=expected_sha256)
    if not v['ok']: return {'restored':False,'verification':v}
    target=Path(target_db_path or DB_PATH); target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(snapshot_path,target); return {'restored':True,'target_db_path':str(target),'verification':v,'restored_at_ms':_now_ms()}
