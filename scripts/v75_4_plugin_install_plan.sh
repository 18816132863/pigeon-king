#!/bin/bash
# V75.4 Plugin Install Plan
# OpenClaw 推荐插件安装计划

set -e

echo "============================================================"
echo "V75.4 Plugin Install Plan"
echo "============================================================"

# 1. 安装 node-pty（终端支持）
echo ""
echo "[1] 安装 @lydell/node-pty（终端支持）"
echo "    npm install -g @lydell/node-pty"
echo ""

# 2. 安装 better-gateway
echo "[2] 安装 openclaw-better-gateway"
echo "    openclaw plugins install @thisisjeron/openclaw-better-gateway"
echo ""

# 3. 启用 lobster
echo "[3] 启用 lobster（工作流运行时）"
echo "    openclaw plugins enable lobster"
echo ""

# 4. 安装安全类插件
echo "[4] 安装安全类插件"
echo "    openclaw plugins install env-guard"
echo "    openclaw plugins install clawsec"
echo "    openclaw plugins install secureclaw"
echo ""

# 5. 安装记忆类插件
echo "[5] 安装记忆类插件"
echo "    openclaw plugins install cortex-memory"
echo "    openclaw plugins enable memory-lancedb"
echo "    openclaw plugins install lossless-claw"
echo "    openclaw plugins install openclaw-engram"
echo ""

# 6. 安装集成类插件
echo "[6] 安装集成类插件"
echo "    openclaw plugins install composio"
echo ""

# 7. 安装可观测性插件
echo "[7] 安装可观测性插件"
echo "    openclaw plugins install cost-tracker"
echo "    openclaw plugins install manifest"
echo "    openclaw plugins install openclaw-observatory"
echo ""

# 8. 安装开发工具类插件
echo "[8] 安装开发工具类插件"
echo "    openclaw plugins install commit-guard"
echo "    openclaw plugins install dep-audit"
echo "    openclaw plugins install pr-review"
echo "    openclaw plugins install docker-helper"
echo "    openclaw plugins install api-tester"
echo "    openclaw plugins install git-stats"
echo "    openclaw plugins install todo-scanner"
echo "    openclaw plugins install changelog-gen"
echo "    openclaw plugins install file-metrics"
echo ""

# 9. 安装多智能体插件
echo "[9] 安装多智能体插件"
echo "    openclaw plugins install openclaw-foundry"
echo "    openclaw plugins install claude-code-bridge"
echo ""

# 10. 安装实用工具类插件
echo "[10] 安装实用工具类插件"
echo "    openclaw plugins install openclaw-ntfy"
echo "    openclaw plugins install openclaw-sentry-tools"
echo ""

echo "============================================================"
echo "安装计划完成"
echo "============================================================"
echo ""
echo "执行方式："
echo "  1. 手动执行上述命令"
echo "  2. 或运行: bash scripts/v75_4_plugin_install_plan.sh --execute"
echo ""

if [ "$1" == "--execute" ]; then
    echo "开始执行安装..."
    
    # node-pty
    npm install -g @lydell/node-pty || echo "警告: node-pty 安装失败"
    
    # better-gateway
    openclaw plugins install @thisisjeron/openclaw-better-gateway || echo "警告: better-gateway 安装失败"
    
    # 启用 lobster
    openclaw plugins enable lobster || echo "警告: lobster 启用失败"
    
    # 其他插件
    for plugin in env-guard clawsec secureclaw cortex-memory composio cost-tracker manifest openclaw-observatory commit-guard dep-audit pr-review docker-helper api-tester git-stats todo-scanner changelog-gen file-metrics openclaw-foundry claude-code-bridge openclaw-ntfy openclaw-sentry-tools lossless-claw openclaw-engram; do
        openclaw plugins install "$plugin" || echo "警告: $plugin 安装失败"
    done
    
    echo ""
    echo "安装完成，运行检测:"
    python3 scripts/v75_4_plugin_reality_check.py
fi
