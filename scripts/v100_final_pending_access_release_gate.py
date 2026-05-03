#!/usr/bin/env python3
"""
V100 最终发布门 — 使用架构模块重构版本
"""
from __future__ import annotations

import os
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

# 使用架构模块
from governance.gate_kernel import EnvChecker, GateRunner, write_json, safe_jsonable


def main():
    gate = GateRunner("V100_Final_Pending_Access_Release", "V100.0")

    # 检查 1: 环境变量
    env = EnvChecker.check_all()
    print(f"  OFFLINE_MODE={env.get('OFFLINE_MODE')}")
    print(f"  NO_EXTERNAL_API={env.get('NO_EXTERNAL_API')}")

    # 检查 2: 打包完整性
    pkg = ROOT / "reports/V100_PACKAGING_INTEGRITY_GATE.json"
    pkg_ok = pkg.exists()
    print(f"  Packaging gate: {'present' if pkg_ok else 'missing'}")

    # 检查 3: V97 长稳
    v97 = ROOT / "reports/V97_LONG_RUN_STABILITY_GATE.json"
    v97_ok = v97.exists()
    print(f"  V97 Long run: {'present' if v97_ok else 'missing'}")

    # 检查 4: V99 融合
    v99 = ROOT / "reports/V99_DIRECTORY_FUSION_AND_CLEANUP_GATE.json"
    v99_ok = v99.exists()
    print(f"  V99 Fusion: {'present' if v99_ok else 'missing'}")

    # 检查 5: 真实世界隔离
    real_world_not_connected = env.get("NO_REAL_SEND") and env.get("NO_REAL_PAYMENT") and env.get("NO_REAL_DEVICE")
    all_env_ok = all(env.values())

    result = {
        "version": "V100.0",
        "status": "pass" if (all_env_ok and pkg_ok and v97_ok and v99_ok) else "partial",
        "final_pending_access_ready": all_env_ok and pkg_ok and v97_ok and v99_ok,
        "env": env,
        "v97_long_run_present": v97_ok,
        "v99_cleanup_present": v99_ok,
        "packaging_integrity_present": pkg_ok,
        "real_world_connected": not real_world_not_connected,
        "commit_actions_blocked": True,
        "remaining_failures": [],
    }

    if not all_env_ok:
        result["remaining_failures"].append("env_not_fully_isolated")
        result["status"] = "partial"

    write_json(ROOT / "reports/V100_FINAL_PENDING_ACCESS_RELEASE_GATE.json", result)
    print(json.dumps(safe_jsonable(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
