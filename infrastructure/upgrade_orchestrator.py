"""V12.5 final local upgrade gate."""
from __future__ import annotations
import json, tempfile
from pathlib import Path
from typing import Dict, Optional
from infrastructure.release_manifest import build_release_manifest
from infrastructure.slo_monitor import build_slo_report
from infrastructure.platform_adapter.replay_harness import run_default_replay, run_replay_plan, timeout_replay_plan
from infrastructure.platform_adapter.snapshot_manager import create_snapshot, verify_snapshot

def run_upgrade_gate(*, root:str|Path='.', db_path:Optional[Path]=None, output_path:Optional[Path]=None)->Dict:
    root=Path(root).resolve(); db=Path(db_path) if db_path else Path(tempfile.mkdtemp(prefix='pk_v125_'))/'runtime.db'; snapdir=db.parent/'snapshots'
    replay=run_default_replay(db_path=db); timeout_replay=run_replay_plan(timeout_replay_plan(), db_path=db, correlation_id='timeout_replay')
    snap=create_snapshot(db_path=db, snapshot_dir=snapdir, label='v12_5_gate'); snapcheck=verify_snapshot(Path(snap['snapshot_path']), expected_sha256=snap['sha256'])
    slo=build_slo_report(db_path=db, max_blocked_actions=1); manifest=build_release_manifest(root=root, db_path=db)
    blocking=[]
    if replay.get('gate')!='pass': blocking.append('default_replay_failed')
    if timeout_replay.get('gate')!='pass': blocking.append('timeout_replay_failed')
    if not snapcheck.get('ok'): blocking.append('snapshot_verification_failed')
    if slo.get('gate')=='fail': blocking.append('slo_gate_failed')
    if manifest.get('release_gate')!='pass': blocking.append('base_release_manifest_failed')
    report={'version':'V12.5','upgrade_gate':'pass' if not blocking else 'fail','blocking_items':blocking,'db_path':str(db),'checks':{'default_replay':replay,'timeout_replay':timeout_replay,'snapshot':snap,'snapshot_check':snapcheck,'slo':slo,'base_release_manifest':{'version':manifest.get('version'),'release_gate':manifest.get('release_gate'),'blocking_items':manifest.get('blocking_items'),'file_digest':manifest.get('file_manifest',{}).get('digest'),'file_count':manifest.get('file_manifest',{}).get('file_count')}}}
    if output_path: Path(output_path).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
