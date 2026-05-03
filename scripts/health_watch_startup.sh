#!/bin/bash
# OpenClaw Health Watch 自启动脚本
# 通过 crontab @reboot 触发，确保系统重启后自动拉起守护

LOG_DIR="/home/sandbox/.openclaw/workspace/logs"
mkdir -p "$LOG_DIR"

# 检查是否已在运行
if pgrep -f "health_watch.py.*--watch" > /dev/null; then
    echo "[$(date)] health_watch 已在运行，跳过" >> "$LOG_DIR/health_watch_startup.log"
    exit 0
fi

echo "[$(date)] 启动 health_watch 守护进程..." >> "$LOG_DIR/health_watch_startup.log"
nohup /usr/bin/python3 /home/sandbox/.openclaw/workspace/scripts/health_watch.py --watch 900 \
    >> "$LOG_DIR/health_watch.log" 2>&1 &

echo "[$(date)] PID: $!" >> "$LOG_DIR/health_watch_startup.log"
