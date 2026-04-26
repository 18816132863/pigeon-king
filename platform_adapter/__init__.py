"""
Platform Adapter Layer - 平台适配层
提供平台能力探测、连接状态判断、自动降级策略。
"""

from .base import PlatformAdapter, PlatformCapability
from .null_adapter import NullAdapter
from .runtime_probe import RuntimeProbe
from .xiaoyi_adapter import XiaoyiAdapter
from .connection_state import DeviceConnectionState, probe_device_connection

try:
    from config import (
        load_capability_timeouts,
        load_dual_push_config,
        DefaultSkillConfig,
        FeatureFlags,
    )
    CAPABILITY_TIMEOUTS = load_capability_timeouts()
    DUAL_PUSH_CONFIG = load_dual_push_config()
    _default_skill_cfg = DefaultSkillConfig() if DefaultSkillConfig else None
    _feature_flags = FeatureFlags() if FeatureFlags else None
except ImportError:
    CAPABILITY_TIMEOUTS = {}
    DUAL_PUSH_CONFIG = {}
    _default_skill_cfg = None
    _feature_flags = None

__all__ = [
    'PlatformAdapter', 'PlatformCapability',
    'NullAdapter', 'RuntimeProbe', 'XiaoyiAdapter',
    'DeviceConnectionState', 'probe_device_connection',
    'CAPABILITY_TIMEOUTS', 'DUAL_PUSH_CONFIG',
]
