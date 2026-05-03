"""message_hook_bootstrap — run-level mainline hook integration.

Non-invasive approach:
1. `scripts/mainline_bootstrap.py` handles one-shot registration + cleanup
2. A `.openclaw/hooks/` file tells the runtime to call mainline_hook.run() after every message
3. No modification to core files, no architecture changes

To enable at runtime:
    python3 -m scripts.mainline_bootstrap --enable

To disable:
    python3 -m scripts.mainline_bootstrap --disable
"""
