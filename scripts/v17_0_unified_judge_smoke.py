from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from agent_kernel.unified_judge import UnifiedJudge
j=UnifiedJudge(); ds=[j.decide({'action':'send_external','external':True},{'no_auto_external_send':True}),j.decide({'action':'noop'}),j.decide({'action':'disable_safety'})]; assert [d.decision for d in ds]==['require_approval','allow','block']; print(json.dumps({'v17_0_unified_judge':'pass','decisions':[d.decision for d in ds]},ensure_ascii=False))
