#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

from core.device_timeout_resilience import run_top_operator_v26

def main() -> int:
    msg = " ".join(sys.argv[1:]).strip() or "端侧 Calendar 读取大量日程，容易超过60秒，改成可恢复执行"
    report = run_top_operator_v26(msg, source="cli", user_id="local_user", root=".top_ai_operator_v26_cli_state")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
