# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件 - Verdent AI 自动注册脚本
用于将 Python 脚本打包成独立的 Windows 可执行文件
"""

block_cipher = None

a = Analysis(
    ['verdent_auto_register.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'DrissionPage',
        'DrissionPage.chromium_page',
        'DrissionPage.chromium_options',
        'requests',
        'urllib3',
        'charset_normalizer',
        'idna',
        'certifi',
        'json',
        'uuid',
        'datetime',
        'concurrent.futures',
        're',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='verdent_auto_register',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 隐藏控制台窗口 (无窗口模式)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加自定义图标
)

