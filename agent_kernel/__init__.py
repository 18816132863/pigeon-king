# V104 compatibility wrapper for legacy agent_kernel imports.
# Do not place runtime logic here; use orchestration.agent_kernel as source of truth.
try:
    from orchestration.agent_kernel import *  # type: ignore
except Exception:
    pass
