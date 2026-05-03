# V104.2: best-effort offline guard activation for normal Python runs.
# Note: python -S disables sitecustomize, so gates still import the guard explicitly.
try:
    from infrastructure.offline_runtime_guard import activate
    activate(reason="sitecustomize")
except Exception:
    pass
