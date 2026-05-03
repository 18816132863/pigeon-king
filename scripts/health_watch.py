#!/usr/bin/env python3
"""
健康监控守护脚本 — 持续巡检 + 告警

功能：
- 按间隔轮询系统状态
- 与上次结果对比，发现故障则输出告警
- 可选 --daemon 后台运行
- 可选 --notify 发送告警通知到通道

用法：
  python3 scripts/health_watch.py                       # 单次巡检
  python3 scripts/health_watch.py --watch 60            # 每60秒轮询一次（前台）
  python3 scripts/health_watch.py --daemon              # 后台守护运行
"""

import json
import os
import sys
import time
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple


ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "reports" / "health"
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "watch_state.json"
ALERT_LOG = STATE_DIR / "alert_log.json"


def check_disk() -> float:
    try:
        import shutil
        usage = shutil.disk_usage("/")
        return usage.used / usage.total * 100
    except:  # noqa: E722
        return 0.0


def check_memory() -> float:
    try:
        out = subprocess.run(["free"], capture_output=True, text=True).stdout
        lines = out.split("\n")
        for line in lines:
            if line.startswith("Mem:"):
                parts = line.split()
                total, used = float(parts[1]), float(parts[2])
                return round(used / total * 100, 1)
        return 0.0
    except:  # noqa: E722
        return 0.0


def check_gateway() -> Dict[str, Any]:
    try:
        out = subprocess.run(["openclaw", "gateway", "status"], capture_output=True, text=True, timeout=10)
        stdout = out.stdout
        stderr = out.stderr
        ok = "ok" in stdout.lower() or "running" in stdout.lower()
        return {"status": "ok" if ok else "error", "output": (stdout + stderr)[:200]}
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "timeout"}
    except Exception as e:
        return {"status": "error", "output": str(e)}


def check_imports() -> List[Dict]:
    """检查关键模块 import"""
    sys.path.insert(0, str(ROOT))
    checks = [
        ("core.llm.model_registry", "ModelRegistry"),
        ("core.llm.model_router", "auto_route"),
        ("governance.embodied_pending_state", "CommitBarrier"),
        ("infrastructure.execution_runtime", "RealExecutionBroker"),
        ("orchestration.final_pending_release", "V85FinalPendingAccessKernel"),
    ]
    results = []
    for module, name in checks:
        try:
            mod = __import__(module, fromlist=[name])
            obj = getattr(mod, name, None)
            results.append({"module": module, "name": name, "ok": obj is not None})
        except Exception as e:
            results.append({"module": module, "name": name, "ok": False, "error": str(e)[:80]})
    return results


def check_daemon() -> Dict[str, Any]:
    """检查健康监控守护进程是否在运行"""
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split("\n"):
            if "health_watch.py" in line and "--watch" in line and "grep" not in line:
                parts = line.split()
                pid = parts[1] if len(parts) > 1 else "?"
                return {"status": "running", "pid": pid}
    except:  # noqa: E722
        pass
    return {"status": "stopped", "pid": None}


def snapshot() -> Dict[str, Any]:
    gateway = check_gateway()
    imports = check_imports()
    disk = check_disk()
    mem = check_memory()
    daemon = check_daemon()
    ts = datetime.now().isoformat()

    return {
        "timestamp": ts,
        "disk_percent": disk,
        "memory_percent": mem,
        "gateway": gateway,
        "daemon": daemon,
        "imports": imports,
        "all_ok": (
            gateway["status"] == "ok"
            and all(i["ok"] for i in imports)
            and disk < 90
            and mem < 90
        ),
    }


def diff_state(old: Dict, new: Dict) -> List[str]:
    changes = []
    # Gateway change
    if old.get("gateway", {}).get("status") != new.get("gateway", {}).get("status"):
        changes.append(f"Gateway: {old.get('gateway', {}).get('status', '?')} → {new.get('gateway', {}).get('status', '?')}")

    # Daemon change
    old_daemon = old.get("daemon", {}).get("status")
    new_daemon = new.get("daemon", {}).get("status")
    if old_daemon != new_daemon:
        changes.append(f"健康监控守护: {old_daemon or '?'} → {new_daemon or '?'}")

    # Disk change
    old_disk = old.get("disk_percent", 0)
    new_disk = new.get("disk_percent", 0)
    if abs(new_disk - old_disk) > 5:
        changes.append(f"磁盘: {old_disk:.1f}% → {new_disk:.1f}%")

    # Memory change
    old_mem = old.get("memory_percent", 0)
    new_mem = new.get("memory_percent", 0)
    if abs(new_mem - old_mem) > 5:
        changes.append(f"内存: {old_mem:.1f}% → {new_mem:.1f}%")

    # Import status
    old_imports = {i["name"]: i["ok"] for i in old.get("imports", [])}
    new_imports = {i["name"]: i["ok"] for i in new.get("imports", [])}
    for name in set(list(old_imports.keys()) + list(new_imports.keys())):
        ok_old = old_imports.get(name, None)
        ok_new = new_imports.get(name, None)
        if ok_old is not None and ok_new is not None and ok_old != ok_new:
            changes.append(f"模块 {name}: {'✅' if ok_old else '❌'} → {'✅' if ok_new else '❌'}")

    # All-ok toggle
    if old.get("all_ok") and not new.get("all_ok"):
        changes.append("⚠️ 系统状态从正常变为异常！")

    return changes


def log_alert(changes: List[str], state: Dict):
    if not changes:
        return
    alerts = []
    if ALERT_LOG.exists():
        try:
            alerts = json.loads(ALERT_LOG.read_text())
        except:  # noqa: E722
            alerts = []
    alerts.append({
        "timestamp": datetime.now().isoformat(),
        "changes": changes,
        "state": state.get("all_ok"),
    })
    # Keep last 100
    alerts = alerts[-100:]
    ALERT_LOG.write_text(json.dumps(alerts, ensure_ascii=False, indent=2))


def load_previous() -> Dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:  # noqa: E722
            return {}
    return {}


def run_once(verbose: bool = True) -> Dict:
    state = snapshot()
    prev = load_previous()
    changes = diff_state(prev, state)
    if changes:
        log_alert(changes, state)

    if verbose:
        daemon_status = state.get("daemon", {}).get("status", "?")
        daemon_pid = state.get("daemon", {}).get("pid", "")
        daemon_str = f"守护:{daemon_status}" if daemon_status == "running" else "⚠️守护:未运行"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 磁盘:{state['disk_percent']:.0f}% 内存:{state['memory_percent']:.0f}% "
              f"Gateway:{state['gateway']['status']} "
              f"{daemon_str} "
              f"模块:{sum(1 for i in state['imports'] if i['ok'])}/{len(state['imports'])}", end="")
        if state['all_ok'] and daemon_status == "running":
            print(" ✅")
        else:
            print(" ⚠️")
        if daemon_status != "running":
            print(f"   启动: nohup python3 scripts/health_watch.py --watch 900 > /tmp/health_watch.log 2>&1 &")
        if changes:
            print(f"   变更: {'; '.join(changes)}")

    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    return state


def main():
    import argparse
    parser = argparse.ArgumentParser(description="健康监控守护")
    parser.add_argument("--watch", type=int, default=0, help="轮询间隔（秒），0=单次")
    parser.add_argument("--daemon", action="store_true", help="后台守护运行")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    global STATE_FILE
    STATE_FILE = STATE_DIR / f"watch_state_{datetime.now().strftime('%Y%m%d')}.json"

    if args.json:
        state = run_once(verbose=False)
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0 if state["all_ok"] else 1

    if args.daemon:
        # Fork to background
        pid = os.fork()
        if pid > 0:
            print(f"[PID {pid}] 后台守护已启动，日志: {ALERT_LOG}")
            sys.exit(0)
        # Child process
        os.setsid()
        interval = args.watch if args.watch > 0 else 60
        while True:
            run_once()
            time.sleep(interval)
    elif args.watch > 0:
        interval = max(10, args.watch)
        print(f"轮询中 (每 {interval} 秒)... Ctrl+C 退出")
        try:
            STATE_FILE = STATE_DIR / f"watch_state_{datetime.now().strftime('%Y%m%d')}.json"
            while True:
                run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n监控已停止")
    else:
        state = run_once()
        return 0 if state["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
