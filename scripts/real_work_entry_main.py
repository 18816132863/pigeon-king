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

from core.real_work_entry import run_real_work_entry
from core.real_work_entry.schemas import to_dict

def main() -> int:
    msg = " ".join(sys.argv[1:]).strip() or "整理当前任务并给出可执行计划"
    report = run_real_work_entry(msg, source="cli", user_id="local_user", root=".real_work_entry_cli_state")
    print(json.dumps(to_dict(report), ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
