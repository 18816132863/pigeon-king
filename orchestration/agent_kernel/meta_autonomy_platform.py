"""Bridge entrypoint for V257-V316 meta autonomy platform."""

from core.meta_autonomy_platform import (
    MetaAutonomyPlatformKernel,
    init_meta_autonomy_platform,
    run_meta_autonomy_platform_cycle,
)

__all__ = ["MetaAutonomyPlatformKernel", "init_meta_autonomy_platform", "run_meta_autonomy_platform_cycle"]
