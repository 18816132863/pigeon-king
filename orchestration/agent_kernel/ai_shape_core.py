"""Final unified AI-shape bridge.

All future user messages should be allowed to enter through AIShapeCore/YuanLingSystem
before reaching older V85-V316 subsystems.
"""

from core.ai_shape_core import AIShapeCore, YuanLingSystem, init_ai_shape_core, run_ai_shape_cycle

__all__ = ["AIShapeCore", "YuanLingSystem", "init_ai_shape_core", "run_ai_shape_cycle"]
