#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windsurf 自动登录脚本 - 直接操作扩展存储
通过修改 VS Code 扩展的本地存储来实现自动登录
"""

import hashlib
import base64
import secrets
import requests
import webbrowser
import urllib.parse
import json
import os
import time
import sqlite3
from pathlib import Path
from typing import Optional, Tuple


class WindsurfAutoLogin:
    """Windsurf自动登录处理类 - 操作扩展存储版本"""
    
    def __init__(self, token: str):
        """
        初始化登录处理器
        
        Args:
            token: Verdent认证token (从cookie中获取)
        """
        self.token = token
        self.auth_url = "https://login.verdent.ai/passport/pkce/auth"
        self.callback_scheme = "windsurf://verdentai.verdent/auth"
        
        # 定位 Windsurf 存储目录
        self.storage_dir = self._find_storage_dir()
        
    def _find_storage_dir(self) -> Optional[Path]:
        """
        查找 Windsurf 扩展的存储目录
        
        Returns:
            存储目录路径或None
        """
        # Windows 路径
        appdata = os.getenv('APPDATA')
        if not appdata:
            print("✗ 无法获取 APPDATA 环境变量")
            return None
        
        # 可能的路径
        possible_paths = [
            Path(appdata) / "Windsurf" / "User" / "globalStorage" / "verdentai.verdent",
            Path(appdata) / "Code" / "User" / "globalStorage" / "verdentai.verdent",
            Path(appdata) / "VSCode" / "User" / "globalStorage" / "verdentai.verdent",
        ]
        
        for path in possible_paths:
            if path.exists():
                print(f"✓ 找到扩展存储目录: {path}")
                return path
        
        print("✗ 未找到扩展存储目录")
        print("  尝试的路径:")
        for path in possible_paths:
            print(f"    - {path}")
        return None
        
    def _write_to_storage(self, key: str, value: str) -> bool:
        """
        写入数据到扩展存储（尝试多种方式）
        
        Args:
            key: 存储键
            value: 存储值
            
        Returns:
            是否成功
        """
        if not self.storage_dir:
            print("✗ 存储目录未找到，无法写入")
            return False
        
        try:
            # 方法1: 尝试写入 state.vscdb (VS Code 的 SQLite 数据库)
            db_file = self.storage_dir.parent.parent / "state.vscdb"
            if db_file.exists():
                try:
                    conn = sqlite3.connect(str(db_file))
                    cursor = conn.cursor()
                    
                    # VS Code 使用 ItemTable 存储数据
                    cursor.execute("""
                        INSERT OR REPLACE INTO ItemTable (key, value)
                        VALUES (?, ?)
                    """, (f"verdent_{key}", value))
                    
                    conn.commit()
                    conn.close()
                    print(f"✓ 成功写入到数据库: verdent_{key}")
                    return True
                except Exception as e:
                    print(f"  数据库写入失败: {e}")
            
            # 方法2: 创建 JSON 文件
            storage_file = self.storage_dir / f"verdent_{key}.json"
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump({"value": value, "timestamp": int(time.time() * 1000)}, f)
            print(f"✓ 成功写入到文件: {storage_file}")
            return True
            
        except Exception as e:
            print(f"✗ 写入存储失败: {e}")
            return False
    
    def generate_pkce_pair(self) -> Tuple[str, str]:
        """
        生成PKCE验证器和挑战值（完全模拟VS Code扩展的实现）
        
        Returns:
            (code_verifier, code_challenge) 元组
        """
        # 生成随机的code_verifier (32字节 = 64个十六进制字符)
        code_verifier = secrets.token_hex(32)
        
        # 计算code_challenge: BASE64URL(SHA256(code_verifier))
        # 注意：必须使用标准base64然后手动替换，而不是直接用urlsafe_b64encode
        sha256_hash = hashlib.sha256(code_verifier.encode('ascii')).digest()
        code_challenge = base64.b64encode(sha256_hash).decode('ascii')
        
        # 手动转换为 URL-safe Base64（与扩展保持一致）
        code_challenge = (code_challenge
                         .replace('+', '-')
                         .replace('/', '_')
                         .rstrip('='))
        
        return code_verifier, code_challenge
    
    def get_authorization_code(self, code_challenge: str) -> Optional[str]:
        """
        通过PKCE challenge获取授权码
        
        Args:
            code_challenge: PKCE挑战值
            
        Returns:
            授权码或None(失败时)
        """
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'token={self.token}',
            'Origin': 'https://www.verdent.ai',
            'Referer': 'https://www.verdent.ai/',
        }
        
        payload = {
            'codeChallenge': code_challenge
        }
        
        try:
            response = requests.post(
                self.auth_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('errCode') == 0:
                    code = data.get('data', {}).get('code')
                    print(f"✓ 成功获取授权码: {code}")
                    return code
                else:
                    print(f"✗ API返回错误: {data.get('errMsg')}")
                    return None
            else:
                print(f"✗ HTTP请求失败: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"✗ 请求异常: {e}")
            return None
    
    def trigger_callback(self, code: str, state: str) -> bool:
        """
        触发 Windsurf 回调
        
        Args:
            code: 授权码
            state: 状态参数(code_verifier)
            
        Returns:
            是否成功
        """
        params = {
            'code': code,
            'state': state
        }
        
        query_string = urllib.parse.urlencode(params)
        callback_url = f"{self.callback_scheme}?{query_string}"
        
        print(f"\n回调 URL:")
        print(f"  {callback_url}\n")
        
        try:
            # 等待一小段时间，确保存储操作完成
            time.sleep(0.5)
            
            webbrowser.open(callback_url)
            print("✓ 已触发 Windsurf 回调")
            return True
        except Exception as e:
            print(f"✗ 触发回调失败: {e}")
            print(f"\n请手动访问此URL: {callback_url}")
            return False
    
    def login(self) -> bool:
        """
        执行完整的自动登录流程
        
        Returns:
            是否成功
        """
        print("=" * 60)
        print("Windsurf 自动登录 - 扩展存储操作版")
        print("=" * 60)
        
        if not self.storage_dir:
            print("\n✗ 无法定位扩展存储目录")
            print("\n提示:")
            print("  1. 确保 Windsurf 已安装并至少运行过一次")
            print("  2. 确认扩展 verdentai.verdent 已安装")
            return False
        
        # 1. 生成PKCE参数
        print("\n[1/5] 生成PKCE参数...")
        code_verifier, code_challenge = self.generate_pkce_pair()
        print(f"  Code Verifier: {code_verifier[:20]}...")
        print(f"  Code Challenge: {code_challenge}")
        
        # 2. 写入 authNonce 到扩展存储
        print("\n[2/5] 写入认证参数到扩展存储...")
        timestamp = str(int(time.time() * 1000))
        
        if not self._write_to_storage("authNonce", code_verifier):
            print("\n⚠ 警告: 无法写入 authNonce，可能会验证失败")
        
        if not self._write_to_storage("authNonceTimestamp", timestamp):
            print("\n⚠ 警告: 无法写入时间戳")
        
        # 3. 获取授权码
        print("\n[3/5] 请求授权码...")
        auth_code = self.get_authorization_code(code_challenge)
        
        if not auth_code:
            print("\n✗ 登录失败: 无法获取授权码")
            return False
        
        # 4. 触发回调
        print("\n[4/5] 触发 Windsurf 回调...")
        if not self.trigger_callback(auth_code, code_verifier):
            return False
        
        # 5. 完成
        print("\n[5/5] 登录流程完成!")
        print("\n✓ 已触发 Windsurf 自动登录")
        print("\n说明:")
        print("  1. 脚本已将认证参数写入扩展存储")
        print("  2. 已触发 windsurf:// 回调 URL")
        print("  3. Windsurf 应该会自动完成登录")
        print("\n注意:")
        print("  如果登录失败，可能是因为:")
        print("  - 扩展存储目录权限不足")
        print("  - 存储格式与扩展版本不匹配")
        print("  - 需要先关闭 Windsurf 再运行脚本")
        
        return True


def main():
    """主函数"""
    print("请输入你的Verdent Token:")
    print("(可以从浏览器Cookie中获取 'token' 字段的值)")
    print()
    
    # 从用户输入获取token
    token = input("Token: ").strip()
    
    if not token:
        print("\n✗ Token不能为空!")
        return
    
    print("\n重要提示:")
    print("  为了确保存储操作成功，建议:")
    print("  1. 先关闭 Windsurf")
    print("  2. 运行此脚本")
    print("  3. 脚本会自动启动 Windsurf 并完成登录")
    print()
    
    # 执行登录
    login_handler = WindsurfAutoLogin(token)
    success = login_handler.login()
    
    if success:
        print("\n" + "=" * 60)
        print("自动登录流程已触发!")
        print("=" * 60)
        print("\n请观察 Windsurf 是否自动完成登录。")
    else:
        print("\n" + "=" * 60)
        print("登录失败")
        print("=" * 60)


if __name__ == "__main__":
    main()
