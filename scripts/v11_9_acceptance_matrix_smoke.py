#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from infrastructure.acceptance_matrix import run_acceptance_matrix

td = tempfile.mkdtemp(prefix='pk_v119_')
report = run_acceptance_matrix(db_path=Path(td) / 'runtime.db')
assert report['gate'] == 'pass', report
print(json.dumps({'ok': True, 'version':'V11.9', 'acceptance':report}, ensure_ascii=False, indent=2))
