from __future__ import annotations
import os, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENCLAW_JSON = ROOT / 'openclaw.json'

DEFAULTS = {
    'OFFLINE_MODE': True,
    'NO_EXTERNAL_API': True,
    'DISABLE_LLM_API': True,
    'DISABLE_THINKING_MODE': True,
    'NO_REAL_SEND': True,
    'NO_REAL_PAYMENT': True,
    'NO_REAL_DEVICE': True,
    'bootstrapMaxChars': 8000,
    'bootstrapTotalMaxChars': 32000,
    'contextInjection': 'always',
}

_TRUE = {'1','true','yes','on','y'}
_FALSE = {'0','false','no','off','n'}

def _coerce(v):
    if isinstance(v, str):
        lv = v.strip().lower()
        if lv in _TRUE: return True
        if lv in _FALSE: return False
    return v

class UnifiedRuntimeConfig:
    def __init__(self, root: Path | None = None):
        self.root = root or ROOT
        self.file_config = self._read_file()

    def _read_file(self):
        p = self.root / 'openclaw.json'
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except Exception as e:
            return {'_read_error': str(e)}

    def get(self, key: str, default=None):
        if key in os.environ:
            return _coerce(os.environ[key])
        # support nested runtime dict if present
        for container in (self.file_config, self.file_config.get('runtime', {}) if isinstance(self.file_config, dict) else {}):
            if isinstance(container, dict) and key in container:
                return _coerce(container[key])
        return DEFAULTS.get(key, default)

    def is_offline(self) -> bool:
        return bool(self.get('OFFLINE_MODE', True)) and bool(self.get('NO_EXTERNAL_API', True))

    def no_real_side_effects(self) -> bool:
        return bool(self.get('NO_REAL_SEND', True)) and bool(self.get('NO_REAL_PAYMENT', True)) and bool(self.get('NO_REAL_DEVICE', True))

    def context_budget(self):
        return {
            'bootstrapMaxChars': int(self.get('bootstrapMaxChars', 8000) or 8000),
            'bootstrapTotalMaxChars': int(self.get('bootstrapTotalMaxChars', 32000) or 32000),
            'contextInjection': self.get('contextInjection', 'always'),
            'p0_never_trim': ['safety_red_lines','current_goal','user_preferences','recent_failures','forbidden_actions'],
            'p1_priority': ['persona_state','relationship_summary','available_tools','session_handoff'],
            'p2_trim_allowed': ['old_report_details','vintage_version_details','long_explanations'],
        }

    def summary(self):
        return {
            'offline_mode': self.is_offline(),
            'no_external_api': bool(self.get('NO_EXTERNAL_API', True)),
            'disable_llm_api': bool(self.get('DISABLE_LLM_API', True)),
            'disable_thinking_mode': bool(self.get('DISABLE_THINKING_MODE', True)),
            'no_real_send': bool(self.get('NO_REAL_SEND', True)),
            'no_real_payment': bool(self.get('NO_REAL_PAYMENT', True)),
            'no_real_device': bool(self.get('NO_REAL_DEVICE', True)),
            'no_real_side_effects': self.no_real_side_effects(),
            'context_budget': self.context_budget(),
        }

def get_runtime_config() -> UnifiedRuntimeConfig:
    return UnifiedRuntimeConfig()
