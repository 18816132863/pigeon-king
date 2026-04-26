from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from agent_kernel.meta_governance import MetaGovernanceGate
data=MetaGovernanceGate().write_report(ROOT/'V23_0_META_GOVERNANCE_REPORT.json'); assert data['status']=='pass'; print(json.dumps({'v23_0_meta_governance':'pass','report':str(ROOT/'V23_0_META_GOVERNANCE_REPORT.json')},ensure_ascii=False))
