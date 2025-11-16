#!/usr/bin/env python3
"""
Verdent AI 一键登录脚本 - 模拟 VS Code 插件登录流程
使用方法: python verdent_auto_login.py <your_token>
"""

import sys
import hashlib
import base64
import secrets
import requests
import json
import subprocess
import platform
import webbrowser
import os
from urllib.parse import quote, urlencode
from pathlib import Path


class VerdentAutoLogin:
    def __init__(self, token, device_id="python-auto-login", app_version="1.0.9"):
        self.token = token
        self.device_id = device_id
        self.app_version = app_version

        # API 端点
        self.auth_page_url = "https://verdent.ai/auth"
        self.pkce_auth_url = "https://login.verdent.ai/passport/pkce/auth"
        self.pkce_callback_url = "https://login.verdent.ai/passport/pkce/callback"

        # 存储 PKCE 参数
        self.code_verifier = None
        self.code_challenge = None
        self.state = None

        # 模拟 VS Code 存储的文件路径
        self.storage_dir = Path.home() / ".verdent_python_storage"
        self.storage_dir.mkdir(exist_ok=True)

        # 定义会影响多账号检测的存储项(身份相关)
        self.identity_storage_keys = [
            # secrets - 认证相关
            "secrets_ycAuthToken",           # 核心认证令牌
            "secrets_verdentApiKey",         # API 密钥
            "secrets_authNonce",             # 认证随机数
            "secrets_authNonceTimestamp",    # 随机数时间戳
            # globalState - 账户信息
            "globalState_userInfo",          # 用户信息(包含订阅状态、token额度等)
            "globalState_taskHistory",       # 任务历史
        ]

        # 定义所有 Verdent AI 扩展的存储项(完全清理)
        self.all_storage_keys = [
            # secrets - 所有加密存储
            "secrets_ycAuthToken",           # 核心认证令牌
            "secrets_verdentApiKey",         # API 密钥
            "secrets_authNonce",             # 认证随机数
            "secrets_authNonceTimestamp",    # 随机数时间戳
            # globalState - 所有全局状态
            "globalState_userInfo",          # 用户信息
            "globalState_apiProvider",       # API 提供商
            "globalState_taskHistory",       # 任务历史
            # workspaceState - 所有工作区状态
            "workspaceState_isPlanMode",     # 计划模式
            "workspaceState_thinkLevel",     # 思考级别
            "workspaceState_selectModel",    # 选择的模型
        ]
        
    def _get_storage_path(self, key_type):
        """获取存储文件路径"""
        return self.storage_dir / f"{key_type}.json"
    
    def _save_storage(self, key_type, data):
        """保存数据到本地存储（模拟 VS Code globalState/secrets）"""
        storage_path = self._get_storage_path(key_type)
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[DEBUG] 已保存 {key_type}: {storage_path}")
    
    def _load_storage(self, key_type):
        """从本地存储读取数据"""
        storage_path = self._get_storage_path(key_type)
        if storage_path.exists():
            with open(storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _delete_storage(self, key_type):
        """删除本地存储（模拟清除操作）"""
        storage_path = self._get_storage_path(key_type)
        if storage_path.exists():
            storage_path.unlink()
            print(f"[DEBUG] 已删除 {key_type}: {storage_path}")
        else:
            print(f"[DEBUG] {key_type} 不存在，无需删除")

    def reset_device_identity(self, generate_new_device_id=True):
        """
        重置设备身份标识，清理所有会影响多账号登录检测的存储项

        Args:
            generate_new_device_id: 是否生成新的设备 ID

        Returns:
            dict: 清理结果统计
        """
        print("\n" + "="*70)
        print("🔄 重置设备身份标识 - 清理多账号检测相关数据")
        print("="*70 + "\n")

        # 统计信息
        stats = {
            "deleted": [],
            "not_found": [],
            "total": 0
        }

        # 1. 清理身份相关的存储文件
        print("[*] 步骤 1: 清理账户身份相关存储...")
        for key in self.identity_storage_keys:
            storage_path = self._get_storage_path(key)
            if storage_path.exists():
                storage_path.unlink()
                stats["deleted"].append(key)
                print(f"    ✓ 已删除: {key}")
            else:
                stats["not_found"].append(key)
                print(f"    - 不存在: {key}")

        stats["total"] = len(stats["deleted"])

        # 2. 重置 API 提供商为默认值
        print("\n[*] 步骤 2: 重置 API 提供商配置...")
        try:
            self._save_storage("globalState_apiProvider", {"value": "openrouter"})
            print("    ✓ API 提供商已重置为: openrouter")
        except Exception as e:
            print(f"    ✗ 重置 API 提供商失败: {e}")

        # 3. 生成新的设备 ID（可选）
        if generate_new_device_id:
            print("\n[*] 步骤 3: 生成新的设备标识...")
            old_device_id = self.device_id
            # 生成基于时间戳的随机设备 ID
            import time
            timestamp = int(time.time() * 1000)
            random_suffix = secrets.token_hex(8)
            self.device_id = f"device-{timestamp}-{random_suffix}"
            print(f"    ✓ 旧设备 ID: {old_device_id}")
            print(f"    ✓ 新设备 ID: {self.device_id}")
        else:
            print("\n[*] 步骤 3: 保持当前设备 ID 不变")
            print(f"    - 当前设备 ID: {self.device_id}")

        # 4. 显示清理摘要
        print("\n" + "="*70)
        print("📊 清理摘要")
        print("="*70)
        print(f"✓ 已删除文件数: {stats['total']}")
        print(f"- 未找到文件数: {len(stats['not_found'])}")

        if stats["deleted"]:
            print("\n已删除的存储项:")
            for key in stats["deleted"]:
                print(f"  • {key}")

        print("\n" + "="*70)
        print("✅ 设备身份重置完成!")
        print("="*70)
        print("\n💡 提示:")
        print("  - 所有账户关联信息已清除")
        print("  - 系统状态已恢复到'全新设备首次登录'")
        print("  - 现在可以使用新账号登录而不会被检测到多账号关联")
        print("  - 建议: 使用不同的 device_id 参数来进一步区分设备\n")

        return stats

    def reset_all_storage(self, generate_new_device_id=True):
        """
        完全清理所有 Verdent AI 扩展的本地存储项

        Args:
            generate_new_device_id: 是否生成新的设备 ID

        Returns:
            dict: 清理结果统计
        """
        print("\n" + "="*70)
        print("⚠️  警告: 完全清理模式")
        print("="*70)
        print("\n此操作将删除所有 Verdent AI 扩展的本地存储数据，包括:")
        print("  • 所有认证信息 (tokens, API keys)")
        print("  • 所有用户信息 (账户、订阅状态)")
        print("  • 所有配置信息 (API 提供商、任务历史)")
        print("  • 所有用户偏好 (计划模式、思考级别、模型选择)")

        print(f"\n将要删除的存储项 (共 {len(self.all_storage_keys)} 项):")
        for i, key in enumerate(self.all_storage_keys, 1):
            print(f"  {i:2d}. {key}")

        print("\n" + "="*70)
        confirm = input("⚠️  确认要删除所有数据吗? (输入 'YES' 确认): ")

        if confirm != "YES":
            print("\n❌ 操作已取消")
            return {"cancelled": True}

        print("\n" + "="*70)
        print("🔄 开始完全清理所有存储...")
        print("="*70 + "\n")

        # 统计信息
        stats = {
            "deleted": [],
            "not_found": [],
            "other_files": [],
            "total": 0,
            "cancelled": False
        }

        # 1. 清理所有存储文件
        print("[*] 步骤 1: 清理所有存储文件...")
        for key in self.all_storage_keys:
            storage_path = self._get_storage_path(key)
            if storage_path.exists():
                storage_path.unlink()
                stats["deleted"].append(key)
                print(f"    ✓ 已删除: {key}")
            else:
                stats["not_found"].append(key)
                print(f"    - 不存在: {key}")

        stats["total"] = len(stats["deleted"])

        # 2. 检查并清理存储目录中的其他文件
        print("\n[*] 步骤 2: 检查存储目录中的其他文件...")
        if self.storage_dir.exists():
            expected_files = {f"{key}.json" for key in self.all_storage_keys}
            for file_path in self.storage_dir.glob("*.json"):
                if file_path.name not in expected_files:
                    stats["other_files"].append(file_path.name)
                    file_path.unlink()
                    print(f"    ✓ 已删除其他文件: {file_path.name}")

        if not stats["other_files"]:
            print("    - 没有其他文件需要清理")

        # 3. 生成新的设备 ID（可选）
        if generate_new_device_id:
            print("\n[*] 步骤 3: 生成新的设备标识...")
            old_device_id = self.device_id
            # 生成基于时间戳的随机设备 ID
            import time
            timestamp = int(time.time() * 1000)
            random_suffix = secrets.token_hex(8)
            self.device_id = f"device-{timestamp}-{random_suffix}"
            print(f"    ✓ 旧设备 ID: {old_device_id}")
            print(f"    ✓ 新设备 ID: {self.device_id}")
        else:
            print("\n[*] 步骤 3: 保持当前设备 ID 不变")
            print(f"    - 当前设备 ID: {self.device_id}")

        # 4. 显示清理摘要
        print("\n" + "="*70)
        print("📊 清理摘要")
        print("="*70)
        print(f"✓ 已删除存储项: {stats['total']} 项")
        print(f"- 未找到存储项: {len(stats['not_found'])} 项")
        print(f"✓ 已删除其他文件: {len(stats['other_files'])} 个")

        if stats["deleted"]:
            print("\n已删除的存储项:")
            for key in stats["deleted"]:
                print(f"  • {key}")

        if stats["other_files"]:
            print("\n已删除的其他文件:")
            for file_name in stats["other_files"]:
                print(f"  • {file_name}")

        if stats["not_found"]:
            print("\n未找到的存储项:")
            for key in stats["not_found"]:
                print(f"  • {key}")

        print("\n" + "="*70)
        print("✅ 完全清理完成!")
        print("="*70)
        print("\n💡 提示:")
        print("  - 所有 Verdent AI 扩展数据已清除")
        print("  - 本地存储已恢复到'从未安装'状态")
        print("  - 所有用户偏好设置已重置")
        print("  - 现在可以重新配置或使用新账号登录\n")

        return stats

    def generate_pkce_params(self):
        """生成 PKCE 参数（模拟 VS Code 插件逻辑）"""
        # 1. 生成 32 字节随机数作为 state 和 code_verifier
        self.state = secrets.token_hex(32)
        self.code_verifier = self.state  # VS Code 插件中使用相同的随机数
        
        # 2. 生成 SHA256 challenge
        challenge_bytes = hashlib.sha256(self.code_verifier.encode('ascii')).digest()
        self.code_challenge = base64.b64encode(challenge_bytes).decode('ascii')
        
        # 3. Base64 URL-safe 编码
        self.code_challenge = (self.code_challenge
                              .replace('+', '-')
                              .replace('/', '_')
                              .rstrip('='))
        
        print(f"[*] 生成 PKCE 参数:")
        print(f"    State: {self.state}")
        print(f"    Code Verifier: {self.code_verifier}")
        print(f"    Code Challenge: {self.code_challenge}")
        
    def build_auth_url(self):
        """构建授权链接（模拟 VS Code 插件生成的链接）"""
        params = {
            'challenge': self.code_challenge,
            'state': self.state,
            'app_id': '1',
            'device_id': self.device_id,
            'app_version': self.app_version,
            'callback': 'vscode://verdentai.verdent/auth'
        }
        
        auth_url = f"{self.auth_page_url}?{urlencode(params)}"
        print(f"\n[*] 授权链接:")
        print(f"    {auth_url}\n")
        return auth_url
    

    def request_auth_code_with_token(self):
        """使用 token 直接请求授权码（跳过浏览器登录步骤）"""
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
            'Cookie': f'token={self.token}',
            'Origin': 'https://www.verdent.ai',
            'Pragma': 'no-cache',
            'Referer': 'https://www.verdent.ai/',
            'Sec-Ch-Ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        }
        
        payload = {
            'codeChallenge': self.code_challenge
        }
        
        print(f"[*] 使用 token 请求授权码...")
        
        response = requests.post(
            self.pkce_auth_url,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errCode') == 0:
                auth_code = result.get('data', {}).get('code')
                print(f"[✓] 授权码获取成功: {auth_code}")
                return auth_code
            else:
                print(f"[×] 请求失败: {result.get('errMsg')}")
                return None
        else:
            print(f"[×] HTTP 请求失败: {response.status_code}")
            print(f"[×] 响应内容: {response.text}")
            return None
    
    def exchange_token(self, auth_code):
        """使用授权码和 code_verifier 交换访问令牌（模拟 VS Code 回调处理）"""
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Content-Type': 'application/json',
            'Origin': 'https://www.verdent.ai',
            'Referer': 'https://www.verdent.ai/',
            'Sec-Ch-Ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        }
        
        payload = {
            'code': auth_code,
            'codeVerifier': self.code_verifier
        }
        
        print(f"[*] 交换访问令牌（模拟 VS Code 回调）...")
        
        response = requests.post(
            self.pkce_callback_url,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errCode') == 0:
                data = result.get('data', {})
                access_token = data.get('token')
                print(f"[✓] 访问令牌获取成功!")
                print(f"\n{'='*60}")
                print(f"访问令牌 (token): {access_token}")
                print(f"{'='*60}\n")
                
                # 保存新的认证信息到本地存储（模拟 VS Code 存储）
                print(f"[*] 保存新的认证信息到本地存储...")
                self._save_storage("secrets_ycAuthToken", {"value": access_token})
                self._save_storage("globalState_apiProvider", {"value": "verdent"})
                
                # 构建模拟的 VS Code 回调 URL
                callback_url = f"vscode://verdentai.verdent/auth?code={auth_code}&state={self.state}"
                print(f"[*] 模拟的 VS Code 回调 URL:")
                print(f"    {callback_url}\n")
                
                return access_token
            else:
                print(f"[×] 令牌交换失败: {result.get('errMsg')}")
                return None
        else:
            print(f"[×] HTTP 请求失败: {response.status_code}")
            print(f"[×] 响应内容: {response.text}")
            return None
    
    def open_vscode_with_callback(self, auth_code):
        """尝试打开 VS Code 并触发回调（可选功能）"""
        callback_url = f"vscode://verdentai.verdent/auth?code={auth_code}&state={self.state}"
        
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(f'start "" "{callback_url}"', shell=True, check=False)
            elif system == "Darwin":  # macOS
                subprocess.run(['open', callback_url], check=False)
            elif system == "Linux":
                subprocess.run(['xdg-open', callback_url], check=False)
            
            print(f"[✓] 已尝试打开 VS Code 回调链接")
            return True
        except Exception as e:
            print(f"[!] 无法自动打开 VS Code: {e}")
            print(f"[*] 请手动复制以下链接到浏览器或 VS Code:")
            print(f"    {callback_url}")
            return False
    
    def login(self, open_vscode=False):
        """执行完整的登录流程"""
        print("\n" + "="*60)
        print("Verdent AI 一键登录脚本 (模拟 VS Code 插件流程)")
        print("="*60 + "\n")
        
        # 步骤 1: 生成 PKCE 参数（模拟 VS Code 插件的 handleSignInWithVerdent）
        self.generate_pkce_params()
        
        # 步骤 2: 构建授权链接（正常流程中会在浏览器打开）
        auth_url = self.build_auth_url()
        
        # 步骤 3: 使用 token 直接请求授权码（跳过浏览器登录）
        print(f"\n[*] 跳过浏览器登录，直接使用 token 获取授权码...")
        auth_code = self.request_auth_code_with_token()
        if not auth_code:
            print("[×] 登录失败: 无法获取授权码")
            return False
        
        # 步骤 4: 交换访问令牌（模拟 VS Code 接收回调）
        access_token = self.exchange_token(auth_code)
        if not access_token:
            print("[×] 登录失败: 无法获取访问令牌")
            return False

        # 步骤 5: （可选）尝试打开 VS Code
        if open_vscode:
            print(f"\n[*] 尝试打开 VS Code...")
            self.open_vscode_with_callback(auth_code)
        
        print("[✓] 登录流程完成!")
        print("\n[*] 流程说明:")
        print("    1. 生成 PKCE 参数 (challenge, state, verifier)")
        print("    2. 构建授权链接 (正常会在浏览器打开)")
        print("    3. 使用 token 直接获取授权码 (跳过浏览器登录)")
        print("    4. 使用授权码交换访问令牌 (模拟 VS Code 回调)")
        print("    5. 登录成功，获得新的访问令牌\n")
        
        print(f"[*] 本地存储位置: {self.storage_dir}")
        print(f"[*] 已保存的文件:")
        for file in self.storage_dir.iterdir():
            print(f"    - {file.name}")
        print()
        
        return True
    



def main():
    # 检查是否为完全清理模式
    if len(sys.argv) >= 2 and sys.argv[1] in ['--reset-all', '--clean-all', '--full-reset']:
        # 检查是否生成新设备 ID
        generate_new_id = '--new-device-id' in sys.argv or '--generate-id' in sys.argv

        # 执行完全清理
        # 使用临时 token 创建实例(清理操作不需要真实 token)
        login_client = VerdentAutoLogin("temp-token-for-cleanup")
        stats = login_client.reset_all_storage(generate_new_device_id=generate_new_id)

        if stats.get("cancelled"):
            sys.exit(0)

        print(f"\n✅ 成功清理 {stats['total']} 个存储项")
        sys.exit(0)

    # 检查是否是设备身份清理模式
    if len(sys.argv) >= 2 and sys.argv[1] in ['--reset-device', '--clean-identity', '--reset']:
        print("\n" + "="*70)
        print("⚠️  警告: 设备身份重置操作")
        print("="*70)
        print("\n此操作将:")
        print("  1. 删除所有账户认证信息")
        print("  2. 清除用户信息缓存")
        print("  3. 重置设备标识(可选)")
        print("  4. 清除任务历史记录")
        print("\n这将使系统恢复到'全新设备首次登录'状态。")

        # 要求用户确认
        confirm = input("\n是否继续? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("\n❌ 操作已取消")
            sys.exit(0)

        # 检查是否生成新设备 ID
        generate_new_id = '--new-device-id' in sys.argv or '--generate-id' in sys.argv

        # 执行清理
        # 使用临时 token 创建实例(清理操作不需要真实 token)
        login_client = VerdentAutoLogin("temp-token-for-cleanup")
        stats = login_client.reset_device_identity(generate_new_device_id=generate_new_id)

        print(f"\n✅ 成功清理 {stats['total']} 个存储项")
        sys.exit(0)

    # 正常登录模式
    if len(sys.argv) < 2:
        print("使用方法: python verdent_auto_login.py <your_token> [选项]")
        print("\n" + "="*70)
        print("=== 登录模式 ===")
        print("="*70)
        print("  <your_token>              你的 Verdent AI token")
        print("  --open-vscode             (可选) 尝试打开 VS Code 触发回调")

        print("\n" + "="*70)
        print("=== 清理模式 ===")
        print("="*70)
        print("  --reset-device            重置设备身份标识(仅清理账户相关数据)")
        print("  --clean-identity          同 --reset-device")
        print("  --reset                   同 --reset-device")
        print("\n  --reset-all               完全清理所有扩展数据(包括用户偏好)")
        print("  --clean-all               同 --reset-all")
        print("  --full-reset              同 --reset-all")

        print("\n" + "="*70)
        print("=== 通用选项 ===")
        print("="*70)
        print("  --new-device-id           清理时生成新的设备 ID")
        print("  --generate-id             同 --new-device-id")

        print("\n" + "="*70)
        print("=== 使用示例 ===")
        print("="*70)
        print("\n1. 登录:")
        print("  python verdent_auto_login.py eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        print("  python verdent_auto_login.py eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... --open-vscode")

        print("\n2. 清理设备身份(推荐用于切换账号):")
        print("  python verdent_auto_login.py --reset-device")
        print("  python verdent_auto_login.py --reset-device --new-device-id")

        print("\n3. 完全清理所有数据(恢复到全新安装状态):")
        print("  python verdent_auto_login.py --reset-all")
        print("  python verdent_auto_login.py --reset-all --new-device-id")

        print("\n" + "="*70)
        print("💡 提示")
        print("="*70)
        print("  • --reset-device: 仅清理账户身份相关数据,保留用户偏好设置")
        print("  • --reset-all:    清理所有数据,包括用户偏好、工作区配置等")
        print("  • --new-device-id: 生成新的设备标识,进一步避免设备关联")
        print("  • 切换账号前建议使用 --reset-device 避免多账号检测")
        print("="*70)
        sys.exit(1)

    token = sys.argv[1]
    open_vscode = '--open-vscode' in sys.argv

    # 执行登录
    login_client = VerdentAutoLogin(token)
    success = login_client.login(open_vscode=open_vscode)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
