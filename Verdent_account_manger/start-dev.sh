#!/bin/bash

echo "========================================"
echo " Verdent账号管理器 - 开发环境启动"
echo "========================================"
echo

cd "$(dirname "$0")"

if [ ! -d "node_modules" ]; then
    echo "[1/2] 安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi
else
    echo "[1/2] 依赖已安装，跳过"
fi

echo
echo "[2/2] 启动开发服务器..."
echo
echo "提示: "
echo "  - 前端会在 http://localhost:5173 启动"
echo "  - Tauri窗口会自动打开"
echo "  - 修改Vue代码会自动热重载"
echo "  - 修改Rust代码需要重启"
echo
echo "按 Ctrl+C 停止服务器"
echo "----------------------------------------"
echo

npm run tauri dev

if [ $? -ne 0 ]; then
    echo
    echo "错误: 启动失败"
    echo
    echo "常见问题:"
    echo "  1. 确保已安装 Rust: https://rustup.rs"
    echo "  2. 确保已安装 Node.js 18+"
    echo "  3. 检查防火墙设置"
    echo "  4. 查看上方错误信息"
    echo
    exit 1
fi
