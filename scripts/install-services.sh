#!/bin/bash
# OpenClaw V10 服务安装脚本
# 将守护进程服务安装到 systemd 并设置自启动
# 需要 root 权限

set -e

SERVICE_FILE="/home/sandbox/.openclaw/workspace/infrastructure/openclaw-daemon.service"
SYSTEMD_DIR="/etc/systemd/system"
HEALTH_USER_SERVICE="/home/sandbox/.config/systemd/user/health-watch.service"

echo "=== OpenClaw V10 服务安装 ==="

# 检查 root
if [ "$(id -u)" -ne 0 ]; then
    echo "⚠️  需要 root 权限安装系统级 systemd 服务"
    echo "   请运行: sudo bash $0"
    echo ""
    echo "   或手动执行:"
    echo "   sudo cp $SERVICE_FILE $SYSTEMD_DIR/"
    echo "   sudo systemctl daemon-reload"
    echo "   sudo systemctl enable openclaw-daemon"
    echo "   sudo systemctl start openclaw-daemon"
    exit 1
fi

# 安装系统级服务（daemon manager，包含健康巡检）
echo "[1/3] 安装 openclaw-daemon.service..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/"

echo "[2/3] 重载 systemd..."
systemctl daemon-reload

echo "[3/3] 启用并启动服务..."
systemctl enable openclaw-daemon
systemctl start openclaw-daemon

echo ""
echo "✅ 安装完成！"
echo "   查看状态: systemctl status openclaw-daemon"
echo "   查看日志: journalctl -u openclaw-daemon -f"
echo "   手动巡检: python3 /home/sandbox/.openclaw/workspace/scripts/health_watch.py"

# 安装用户级 health-watch 作为备用
if [ -f "$HEALTH_USER_SERVICE" ]; then
    echo ""
    echo "📋 用户级 health-watch.service 也已就绪:"
    echo "   systemctl --user enable health-watch.service"
    echo "   systemctl --user start health-watch.service"
fi
