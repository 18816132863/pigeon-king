from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from memory_context.personal_memory_kernel_v4 import PersonalMemoryKernelV4
m = PersonalMemoryKernelV4()
ok = m.write("procedural", "端侧超时后先二次验证再重试", confidence=0.9, source="task_verified")
bad = m.write("semantic", "可能用户喜欢这样", confidence=0.5, source="system_observation")
assert ok["status"] == "written"
assert bad["status"] == "rejected"
print("v29_0_personal_memory_smoke: pass")
