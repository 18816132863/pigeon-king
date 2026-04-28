#!/bin/bash
# V75.6 Plugin Install Plan
# OpenClaw 插件安装计划

set -e

echo "============================================================"
echo "V75.6 Plugin Install Plan"
echo "============================================================"

echo ""
echo "本脚本将安装以下插件："
echo ""
echo "1. lobster (stock) - 工作流运行时"
echo "2. env-guard (skill) - 敏感信息保护"
echo "3. @lydell/node-pty (npm) - 终端支持"
echo ""

if [ "$1" != "--execute" ]; then
    echo "运行方式："
    echo "  bash scripts/v75_6_plugin_install_plan.sh --execute"
    echo ""
    exit 0
fi

echo "开始安装..."
echo ""

# 1. 启用 lobster
echo "[1/3] 启用 lobster..."
openclaw plugins enable lobster 2>&1 || echo "警告: lobster 启用失败"

# 2. 安装 env-guard
echo ""
echo "[2/3] 安装 env-guard..."
openclaw skills install env-guard 2>&1 || echo "警告: env-guard 安装失败"

# 3. 安装 node-pty
echo ""
echo "[3/3] 安装 @lydell/node-pty..."
npm install -g @lydell/node-pty 2>&1 || echo "警告: node-pty 安装失败"

echo ""
echo "============================================================"
echo "安装完成"
echo "============================================================"
echo ""

# 验证安装
echo "验证安装状态..."
python3 scripts/v75_6_plugin_install_check.py
