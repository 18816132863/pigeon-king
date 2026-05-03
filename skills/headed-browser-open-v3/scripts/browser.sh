#!/bin/bash
# browser.sh - 有头浏览器启动/管理脚本 (V3简化版)

CDP_PORT=${CDP_PORT:-18800}
DISPLAY_NUM=${DISPLAY_NUM:-99}
SCREEN_WIDTH=${SCREEN_WIDTH:-1920}
SCREEN_HEIGHT=${SCREEN_HEIGHT:-1080}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCKER_JS="$SCRIPT_DIR/blocker.js"
IDLE_MONITOR="$SCRIPT_DIR/idle-monitor.sh"
ACTIVITY_FILE="/tmp/headed-browser-v3-last-activity"

# 自动检测 Chrome 路径
detect_chrome() {
    if [ -n "$CHROME_PATH" ]; then
        echo "$CHROME_PATH"
        return
    fi

    # 常见 Chrome 路径
    local chrome_paths=(
        "/home/sandbox/chrome-linux/chrome"
        "/opt/chrome-linux/chrome"
        "/usr/bin/google-chrome"
        "/usr/bin/google-chrome-stable"
        "/usr/bin/chromium"
        "/usr/bin/chromium-browser"
        "/opt/google/chrome/google-chrome"
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )

    for path in "${chrome_paths[@]}"; do
        if [ -x "$path" ]; then
            echo "$path"
            return
        fi
    done

    # 尝试 which
    if command -v google-chrome &> /dev/null; then
        command -v google-chrome
        return
    elif command -v google-chrome-stable &> /dev/null; then
        command -v google-chrome-stable
        return
    elif command -v chromium &> /dev/null; then
        command -v chromium
        return
    elif command -v chromium-browser &> /dev/null; then
        command -v chromium-browser
        return
    fi

    echo "Error: Chrome not found. Please install Google Chrome or Chromium." >&2
    exit 1
}

start_browser() {
    local url="$1"
    
    # 检查是否已运行
    if pgrep -f "chrome.*remote-debugging-port=$CDP_PORT" > /dev/null; then
        echo "浏览器已在运行 (CDP端口: $CDP_PORT)"
        
        # 如果提供了 URL，使用 CDP 打开新标签页
        if [ -n "$url" ]; then
            echo "正在打开新标签页: $url"
            
            # 获取第一个页面的 WebSocket URL
            local ws_url=$(curl -s "http://127.0.0.1:$CDP_PORT/json" | python3 -c "import sys, json; pages = json.load(sys.stdin); print([p for p in pages if p.get('type') == 'page'][0].get('webSocketDebuggerUrl', ''))" 2>/dev/null)
            
            if [ -n "$ws_url" ]; then
                # 使用 CDP 创建新标签页
                python3 << PYEOF
import json
import sys
try:
    import websocket
    ws = websocket.create_connection("$ws_url")
    # 创建新标签页
    cmd = {"id": 1, "method": "Target.createTarget", "params": {"url": "$url"}}
    ws.send(json.dumps(cmd))
    resp = ws.recv()
    result = json.loads(resp)
    ws.close()
    if "result" in result and "targetId" in result["result"]:
        print(f"新标签页已创建: {result['result']['targetId']}")
        sys.exit(0)
    else:
        print(f"创建标签页失败: {result}", file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f"错误: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
                if [ $? -eq 0 ]; then
                    return 0
                fi
            fi
            
            echo "CDP 打开失败，尝试使用 xdg-open..."
            DISPLAY=:$DISPLAY_NUM xdg-open "$url" 2>/dev/null || echo "无法打开新标签页"
        fi
        return 0
    fi
    
    # 用户数据目录（使用固定路径，避免 $$ 导致的目录变化问题）
    USER_DATA_DIR="/tmp/chrome-headed-v3-data"
    mkdir -p "$USER_DATA_DIR"
    
    # 创建 Preferences 文件，禁用会话恢复和崩溃提示
    PREFS_DIR="$USER_DATA_DIR/Default"
    mkdir -p "$PREFS_DIR"
    cat > "$PREFS_DIR/Preferences" << 'PREFS_EOF'
{
    "profile": {
        "default_content_setting_values": {
            "protocol_handler": 2
        }
    },
    "session": {
        "restore_on_startup": 5,
        "startup_urls": ["about:blank"]
    },
    "browser": {
        "enabled_labs_experiments": [
            "disable-external-intent-requests@2"
        ]
    }
}
PREFS_EOF
    
    # 清除会话恢复信息，防止"Restore pages"提示和恢复之前的标签页
    rm -rf "$USER_DATA_DIR/Singleton*" 2>/dev/null || true
    rm -f "$USER_DATA_DIR/Last*" 2>/dev/null || true
    rm -f "$USER_DATA_DIR/*_startup_log*" 2>/dev/null || true
    rm -rf "$USER_DATA_DIR/Default/Sessions" 2>/dev/null || true
    rm -f "$USER_DATA_DIR/Default/Current*" 2>/dev/null || true
    rm -f "$USER_DATA_DIR/Default/Last*" 2>/dev/null || true
    
    # 检测 Chrome 路径
    local chrome_path
    chrome_path=$(detect_chrome)
    
    # 构建 Chrome 启动参数字符串
    local chrome_args_str="--no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu --disable-web-security --disable-features=IsolateOrigins,site-per-process --remote-debugging-port=$CDP_PORT --window-size=$SCREEN_WIDTH,$SCREEN_HEIGHT --force-device-scale-factor=1 --disable-blink-features=AutomationControlled --disable-popup-blocking --no-first-run --no-default-browser-check --user-data-dir=$USER_DATA_DIR --remote-allow-origins=* --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-background-networking --disable-breakpad --disable-client-side-phishing-detection --disable-component-update --disable-default-apps --disable-hang-monitor --disable-ipc-flooding-protection --disable-prompt-on-repost --disable-sync --force-color-profile=srgb --metrics-recording-only --safebrowsing-disable-auto-update --password-store=basic --use-mock-keychain --enable-automation --disable-session-crashed-bubble --disable-restore-session-state"
    
    # 如果提供了URL，添加协议拦截脚本
    if [ -n "$url" ]; then
        if [ -f "$BLOCKER_JS" ]; then
            chrome_args_str="$chrome_args_str --inject-js=$BLOCKER_JS"
        fi
    fi
    
    # 启动 Xvfb（如果未运行）
    if ! pgrep -f "Xvfb.*:$DISPLAY_NUM" > /dev/null; then
        echo "启动 Xvfb :$DISPLAY_NUM..."
        Xvfb :$DISPLAY_NUM -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24 &
        sleep 2
    fi
    
    # 启动 Chrome（后台模式）
    echo "启动 Chrome (CDP端口: $CDP_PORT)..."
    if [ -n "$url" ]; then
        DISPLAY=:$DISPLAY_NUM nohup "$chrome_path" $chrome_args_str "$url" > /tmp/chrome-headed-v3.log 2>&1 &
    else
        DISPLAY=:$DISPLAY_NUM nohup "$chrome_path" $chrome_args_str > /tmp/chrome-headed-v3.log 2>&1 &
    fi
    local chrome_pid=$!
    
    sleep 3
    
    # 验证启动
    if kill -0 $chrome_pid 2>/dev/null || pgrep -f "chrome.*remote-debugging-port=$CDP_PORT" > /dev/null; then
        echo "浏览器启动成功 (PID: $chrome_pid)"
        echo "CDP端口: $CDP_PORT"
        echo "显示: :$DISPLAY_NUM"
        echo "用户数据: $USER_DATA_DIR"
        echo "日志: /tmp/chrome-headed-v3.log"
        [ -n "$url" ] && echo "打开URL: $url"
        
        # 记录活动时间
        touch "$ACTIVITY_FILE"
        
        # 启动空闲监控（如果未运行）
        if [ -f "$IDLE_MONITOR" ] && ! pgrep -f "idle-monitor.sh" > /dev/null; then
            echo "启动空闲监控（1小时无操作自动回收）..."
            nohup "$IDLE_MONITOR" > /tmp/idle-monitor.log 2>&1 &
        fi
        
        return 0
    else
        echo "浏览器启动失败，查看日志: /tmp/chrome-headed-v3.log"
        return 1
    fi
}

stop_browser() {
    echo "停止浏览器..."
    pkill -f "chrome.*remote-debugging-port=$CDP_PORT" 2>/dev/null
    pkill -f "Xvfb.*:$DISPLAY_NUM" 2>/dev/null
    echo "已停止"
}

check_status() {
    if pgrep -f "chrome.*remote-debugging-port=$CDP_PORT" > /dev/null; then
        echo "浏览器运行中 (CDP端口: $CDP_PORT)"
        return 0
    else
        echo "浏览器未运行"
        return 1
    fi
}

case "${1:-}" in
    start)
        start_browser "${2:-}"
        ;;
    stop)
        stop_browser
        ;;
    status)
        check_status
        ;;
    *)
        echo "用法: $0 {start [URL]|stop|status}"
        echo ""
        echo "示例:"
        echo "  $0 start                    # 启动浏览器"
        echo "  $0 start https://example.com # 启动并打开网页"
        echo "  $0 status                   # 检查状态"
        echo "  $0 stop                     # 停止浏览器"
        exit 1
        ;;
esac
