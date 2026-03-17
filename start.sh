#!/bin/bash

# Claude Code Usage Monitor - 启动脚本

echo "🚀 Claude Code Usage Monitor"
echo "=============================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    echo "请先安装 Python 3.8 或更高版本"
    exit 1
fi

echo "� 使用本地 Python 环境..."

echo "📥 安装/更新依赖..."
python3 -m pip install -q --user -r requirements.txt || \
python3 -m pip install -q --user --break-system-packages -r requirements.txt || \
echo "⚠️ 依赖安装失败（可能是 PEP 668 / Homebrew Python 限制），继续尝试启动..."

echo ""
echo "✅ 准备就绪！"
echo ""
echo "🌐 启动 Web 服务器..."
echo "📊 访问 http://localhost:5050 查看监控面板"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

python app.py
