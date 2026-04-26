from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from agent_kernel.world_interface import WorldInterfaceRegistry,WorldCapability
r=WorldInterfaceRegistry(); r.register(WorldCapability('local_file_reader','local',scopes=['files','read'])); r.register(WorldCapability('calendar_connector','connector',scopes=['calendar','write'],requires_approval=True,trust_level='approved')); assert r.resolve('file') and r.resolve('calendar',required_scope='write') and r.missing('none'); print(json.dumps({'v18_0_world_interface':'pass'},ensure_ascii=False))
