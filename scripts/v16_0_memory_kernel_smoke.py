from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from agent_kernel.memory_kernel import PersonalMemoryKernel,MemoryRecord
m=PersonalMemoryKernel(':memory:'); m.add(MemoryRecord('pref_once','preference','用户偏好一次性给完整压缩包',['delivery'],.9)); hits=m.search('压缩包',min_confidence=.8); ids=m.writeback_from_task({'goal_id':'goal_demo'},{'success':True}); assert hits and len(ids)==2; print(json.dumps({'v16_0_memory_kernel':'pass','hits':len(hits),'writeback':ids},ensure_ascii=False))
