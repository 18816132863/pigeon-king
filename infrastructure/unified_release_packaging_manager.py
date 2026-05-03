from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'

EXCLUDES = ['__pycache__','.pytest_cache','.repair_state','.backup_','v86_backup_','.venv','venv','node_modules','runtime/tmp','cache']
REQUIRED = ['core','memory_context','infrastructure','governance','orchestration','execution','skills','scripts']

class UnifiedReleasePackagingManager:
    def audit(self):
        missing = [p for p in REQUIRED if not (ROOT/p).exists()]
        offenders=[]
        for p in ROOT.rglob('*'):
            s=str(p.relative_to(ROOT))
            if any(x in s for x in EXCLUDES):
                offenders.append(s)
                if len(offenders)>=100: break
        report={'status':'pass' if not missing else 'partial','missing_required_paths':missing,'runtime_artifacts_sample':offenders,'exclude_patterns':EXCLUDES,'clean_release_exclude_ready':True}
        REPORTS.mkdir(exist_ok=True)
        (REPORTS/'V108_RELEASE_PACKAGING_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        return report

def audit_packaging():
    return UnifiedReleasePackagingManager().audit()
