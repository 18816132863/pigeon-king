"""Bridge entrypoint for V127-V136 release hardening."""

from core.release_hardening import ReleaseHardeningKernel, init_release_hardening, run_release_hardening_cycle

__all__ = ["ReleaseHardeningKernel", "init_release_hardening", "run_release_hardening_cycle"]
