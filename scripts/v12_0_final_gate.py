#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from infrastructure.release_manifest import write_release_manifest

root = Path(__file__).resolve().parents[1]
td = tempfile.mkdtemp(prefix='pk_v120_')
out = root / 'V12_0_RELEASE_MANIFEST.json'
manifest = write_release_manifest(out, root=root, db_path=Path(td) / 'runtime.db')
assert manifest['release_gate'] == 'pass', manifest.get('blocking_items')
print(json.dumps({'ok': True, 'version':'V12.0', 'release_gate':manifest['release_gate'], 'manifest':str(out)}, ensure_ascii=False, indent=2))
