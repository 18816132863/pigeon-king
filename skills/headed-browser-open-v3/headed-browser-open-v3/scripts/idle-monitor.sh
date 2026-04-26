#!/bin/bash
# idle-monitor.sh - 空闲监控和资源回收脚本
# 当 1 小时内没有操作时，自动停止浏览器和 Xvfb

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BROWSER_SH="$SCRIPT_DIR/browser.sh"
PID_FILE="/tmp/headed-browser-v3-monitor.pid"
ACTIVITY_FILE="/tmp/headed-browser-v3-last-activity"
IDLE_TIMEOUT=${IDLE_TIMEOUT:-3600}  # 默认 1 小时（3600秒）
CDP_PORT=${CDP_PORT:-18800}

echo "空闲监控启动 (PID: $$)"
echo "超时时间: ${IDLE_TIMEOUT}秒"

# 保存当前 PID
echo $$ > "$PID_FILE"

# 记录活动时间
touch "$ACTIVITY_FILE"

# 检查是否有活动的 CDP 连接或页面交互
check_activity() {
    local last_activity=$(stat -c %Y "$ACTIVITY_FILE" 2>/dev/null || echo 0)
    local current_time=$(date +%s)
    local idle_time=$((current_time - last_activity))
    
    # 检查浏览器是否还在运行
    if ! pgrep -f "chrome.*remote-debugging-port=$CDP_PORT" > /dev/null; then
        echo "$(date): 浏览器已停止，监控退出"
        rm -f "$PID_FILE"
        exit 0
    fi
    
    # 检查是否超时
    if [ $idle_time -ge $IDLE_TIMEOUT ]; then
        echo "$(date): 空闲 ${idle_time}秒，超过 ${IDLE_TIMEOUT}秒，开始回收资源..."
        "$BROWSER_SH" stop
        rm -f "$PID_FILE" "$ACTIVITY_FILE"
        exit 0
    fi
    
    echo "$(date): 空闲 ${idle_time}秒 / ${IDLE_TIMEOUT}秒"
}

# 主循环
while true; do
    check_activity
    sleep 60  # 每分钟检查一次
done
