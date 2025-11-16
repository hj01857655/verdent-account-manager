#!/bin/bash

echo "========================================"
echo " Verdent账号管理器 - 构建发布版本"
echo "========================================"
echo

cd "$(dirname "$0")"

echo "[1/3] 检查依赖..."
if [ ! -d "node_modules" ]; then
    echo "依赖未安装，开始安装..."
    npm install
    if [ $? -ne 0 ]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi
else
    echo "依赖已安装"
fi

echo
echo "[2/3] 构建前端..."
npm run build
if [ $? -ne 0 ]; then
    echo "错误: 前端构建失败"
    exit 1
fi

echo
echo "[3/3] 构建Tauri应用..."
echo "这可能需要几分钟时间，请耐心等待..."
echo

npm run tauri build

if [ $? -ne 0 ]; then
    echo
    echo "错误: 构建失败"
    exit 1
fi

echo
echo "========================================"
echo " 构建成功！"
echo "========================================"
echo
echo "构建产物位置:"
echo "  src-tauri/target/release/bundle/"
echo

if [ "$(uname)" == "Darwin" ]; then
    echo "macOS安装包:"
    echo "  - DMG: src-tauri/target/release/bundle/dmg/"
    echo "  - APP: src-tauri/target/release/bundle/macos/"
elif [ "$(uname)" == "Linux" ]; then
    echo "Linux安装包:"
    echo "  - DEB: src-tauri/target/release/bundle/deb/"
    echo "  - AppImage: src-tauri/target/release/bundle/appimage/"
fi

echo
