# V104_FINAL_CONSISTENCY_CLEANUP: legacy compatibility wrapper.
# Source of truth: orchestration.agent_kernel.persona_kernel
try:
    from orchestration.agent_kernel.persona_kernel import *  # type: ignore
except Exception as _e:
    __v104_import_error__ = str(_e)
