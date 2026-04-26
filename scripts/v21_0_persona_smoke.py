from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from agent_kernel.persona_kernel import PersonaKernel,PersonaProfile
k=PersonaKernel(PersonaProfile(name='小艺')); ctx=k.apply_to_goal_context({'context_confidence':.9}); assert ctx['persona']['name']=='小艺' and k.policy_profile()['no_auto_external_send']; print(json.dumps({'v21_0_persona':'pass','profile':k.policy_profile()},ensure_ascii=False))
