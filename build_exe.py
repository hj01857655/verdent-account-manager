#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build script for verdent_auto_register.exe
Uses PyInstaller to package with all dependencies
"""

import subprocess
import sys
import os
from pathlib import Path

def build_executable():
    """Build the executable file"""
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("Starting build of verdent_auto_register.exe...")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Single file
        "--console",                     # Console application
        "--clean",                       # Clean temp files
        "--noconfirm",                   # Overwrite output
        "--collect-all", "DrissionPage", # Collect all DrissionPage content
        "--collect-all", "websocket",    # Collect all websocket content
        "--collect-all", "lxml",         # Collect all lxml content
        "--collect-all", "tldextract",   # Collect all tldextract content
        "--hidden-import", "DrissionPage._base.chromium",
        "--hidden-import", "DrissionPage._pages.chromium_page",
        "--hidden-import", "DrissionPage._functions.browser",
        "--hidden-import", "DrissionPage._functions.elements",
        "--hidden-import", "DrissionPage._units.setter",
        "--hidden-import", "DrissionPage._units.waiter",
        "--hidden-import", "websocket._core",
        "--hidden-import", "websocket._app",
        "--hidden-import", "lxml.html",
        "--hidden-import", "lxml.etree",
        "--hidden-import", "cssselect",
        "--hidden-import", "urllib3",
        "--hidden-import", "requests",
        "--hidden-import", "certifi",
        "--hidden-import", "charset_normalizer",
        "--hidden-import", "idna",
        "--name", "verdent_auto_register",
        "verdent_auto_register.py"
    ]
    
    # Add icon if exists
    icon_path = Path("Verdent_account_manger/src-tauri/icons/icon.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # Execute packaging command
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(result.stdout)
        
        # Check output file
        exe_path = Path("dist/verdent_auto_register.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Generated file: {exe_path}")
            print(f"File size: {size_mb:.2f} MB")
            
            # Copy to resources directory
            resources_dir = Path("Verdent_account_manger/resources")
            resources_dir.mkdir(exist_ok=True)
            
            import shutil
            target_path = resources_dir / "verdent_auto_register.exe"
            shutil.copy2(exe_path, target_path)
            print(f"Copied to: {target_path}")
            
            return True
        else:
            print("Error: Generated exe file not found")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
