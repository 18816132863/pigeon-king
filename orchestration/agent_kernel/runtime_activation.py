"""Bridge entrypoint for V137-V146 runtime activation layer."""

from core.runtime_activation import RuntimeActivationKernel, init_runtime_activation, run_runtime_activation_cycle

__all__ = ["RuntimeActivationKernel", "init_runtime_activation", "run_runtime_activation_cycle"]
