from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from capability_extension.controlled_extension_pipeline_v4 import ControlledExtensionPipelineV4, ExtensionCandidate
p = ControlledExtensionPipelineV4()
gap = p.detect_gap("new_tool", ["old_tool"])
assert gap["gap"] is True
ok = p.evaluate_candidate(ExtensionCandidate("new_tool", "reviewed_connector", "reviewed", False))
bad = p.evaluate_candidate(ExtensionCandidate("bad_tool", "random_url", "untrusted", True))
assert ok["decision"] == "candidate_ok"
assert bad["decision"] == "quarantine"
print("v32_0_extension_pipeline_smoke: pass")
