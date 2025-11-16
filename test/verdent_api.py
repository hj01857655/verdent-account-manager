"""
Verdent API - 外部程序调用接口
提供一键退出等功能
"""

import subprocess
from typing import Optional


class VerdentAPI:
    """Verdent VS Code 插件外部控制 API"""
    
    @staticmethod
    def logout(timeout: int = 10) -> bool:
        """
        执行 Verdent 退出登录
        
        Args:
            timeout: 超时时间(秒)
            
        Returns:
            bool: 是否成功
        """
        try:
            result = subprocess.run(
                ["code", "--command", "verdent.logout"],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"✗ 退出超时 (>{timeout}s)")
            return False
        except FileNotFoundError:
            print("✗ 未找到 code 命令,请确保 VS Code 已添加到 PATH")
            return False
        except Exception as e:
            print(f"✗ 退出失败: {e}")
            return False
    
    @staticmethod
    def execute_command(command: str, timeout: int = 10) -> Optional[str]:
        """
        执行任意 VS Code 命令
        
        Args:
            command: 命令名称 (如 "verdent.logout")
            timeout: 超时时间(秒)
            
        Returns:
            str: 命令输出,失败返回 None
        """
        try:
            result = subprocess.run(
                ["code", "--command", command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return None
                
        except Exception as e:
            print(f"✗ 命令执行失败: {e}")
            return None


# 使用示例
if __name__ == "__main__":
    api = VerdentAPI()
    
    print("执行 Verdent 退出...")
    success = api.logout()
    
    if success:
        print("✓ 退出成功")
    else:
        print("✗ 退出失败")
