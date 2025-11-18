import json
import datetime
import requests
import websocket
import threading
import time
from typing import Optional, Dict, Any


class VerdentAPI:
    def __init__(
        self,
        host: str = 'agent.verdent.ai',
        port: int = 443,
        token: Optional[str] = None,
        timeout: int = 10
    ):
        self.host = host
        self.port = port
        self.token = token
        self.timeout = timeout
        
        protocol = 'https' if port == 443 else 'http'
        port_suffix = '' if port in [443, 80] else f':{port}'
        self.base_url = f'{protocol}://{host}{port_suffix}'
        
        self.ws_protocol = 'wss' if port == 443 else 'ws'
        self.ws_url = f'{self.ws_protocol}://{host}{port_suffix}/chat'
    
    def get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.token:
            headers['Cookie'] = f'token={self.token}'
        return headers
    
    def test_api_endpoint(self, endpoint: str, method: str = 'GET') -> tuple:
        """测试API端点的响应"""
        try:
            url = f'{self.base_url}{endpoint}'
            if method == 'GET':
                response = requests.get(
                    url,
                    headers=self.get_headers(),
                    timeout=self.timeout
                )
            else:
                response = requests.post(
                    url,
                    headers=self.get_headers(),
                    timeout=self.timeout,
                    json={}
                )
            
            return response.status_code, response.json() if response.content else None
        except Exception as e:
            return None, str(e)
    
    def test_websocket(self) -> bool:
        """测试WebSocket连接"""
        try:
            ws = websocket.create_connection(
                self.ws_url,
                header=self.get_headers(),
                timeout=5
            )
            ws.close()
            return True
        except Exception as e:
            print(f"  WebSocket连接失败: {str(e)}")
            return False


def test_account_capabilities(token, label):
    """深度测试账号的各项功能"""
    print(f"\n{'='*70}")
    print(f"  {label} - 功能测试")
    print('='*70)
    
    api = VerdentAPI(token=token)
    results = {}
    
    # 测试常用API端点
    endpoints = [
        ('/user/center/info', 'GET', '用户信息'),
        ('/user/center/quota', 'GET', '配额信息'),
        ('/user/center/usage', 'GET', '使用情况'),
        ('/input_box/info', 'GET', '输入框信息'),
        ('/chat/models', 'GET', '可用模型'),
        ('/chat/conversations', 'GET', '会话列表'),
        ('/user/center/settings', 'GET', '用户设置'),
    ]
    
    print("\n【API端点测试】")
    for endpoint, method, name in endpoints:
        status_code, response = api.test_api_endpoint(endpoint, method)
        if status_code:
            success = status_code < 400
            results[endpoint] = success
            symbol = "✓" if success else "✗"
            print(f"  {symbol} {name:<15} [{endpoint:<30}] : {status_code}")
            
            # 如果有特殊数据，显示出来
            if success and response and isinstance(response, dict):
                data = response.get('data', {})
                if endpoint == '/chat/models' and data:
                    models = data.get('models', []) if isinstance(data, dict) else data
                    if models:
                        print(f"    可用模型: {', '.join(models[:3])}...")
                elif endpoint == '/user/center/quota' and data:
                    print(f"    配额: {data}")
        else:
            results[endpoint] = False
            print(f"  ✗ {name:<15} [{endpoint:<30}] : 连接错误 - {response}")
    
    # 测试WebSocket连接
    print("\n【WebSocket连接测试】")
    ws_result = api.test_websocket()
    results['websocket'] = ws_result
    print(f"  {'✓' if ws_result else '✗'} WebSocket连接: {'成功' if ws_result else '失败'}")
    
    # 测试特殊功能
    print("\n【特殊功能测试】")
    
    # 测试创建会话
    status_code, response = api.test_api_endpoint('/chat/conversation', 'POST')
    can_create_conversation = status_code and status_code < 400
    results['create_conversation'] = can_create_conversation
    print(f"  {'✓' if can_create_conversation else '✗'} 创建会话: {'允许' if can_create_conversation else '禁止'}")
    
    return results


def compare_capabilities(results1, results2):
    """对比两个账号的功能差异"""
    print(f"\n{'='*70}")
    print("  功能差异对比")
    print('='*70)
    
    all_keys = set(results1.keys()) | set(results2.keys())
    differences = []
    
    for key in sorted(all_keys):
        val1 = results1.get(key, None)
        val2 = results2.get(key, None)
        
        if val1 != val2:
            differences.append((key, val1, val2))
    
    if differences:
        print("\n【发现功能差异】")
        for key, val1, val2 in differences:
            status1 = "可用" if val1 else "不可用"
            status2 = "可用" if val2 else "不可用"
            print(f"  • {key}:")
            print(f"    - 正常账号: {status1}")
            print(f"    - 异常账号: {status2}")
    else:
        print("\n  ✓ 两个账号的功能完全相同，未发现差异")
    
    # 统计
    print(f"\n【功能统计】")
    working1 = sum(1 for v in results1.values() if v)
    working2 = sum(1 for v in results2.values() if v)
    print(f"  正常账号: {working1}/{len(results1)} 个功能正常")
    print(f"  异常账号: {working2}/{len(results2)} 个功能正常")


def main():
    # 定义两个token
    normal_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjU2MTY0MzM4ODkyODAsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU4Nzc4OTIsImlhdCI6MTc2MzI4NTg5MiwibmJmIjoxNzYzMjg1ODkyfQ.xL1UUy032DzbW9vVgWKOkdvk0ZWZeQfKa0fPxIrqo-U"
    abnormal_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjMwNDA3ODU2NDU1NjgsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU3MjgzNzEsImlhdCI6MTc2MzEzNjM3MSwibmJmIjoxNzYzMTM2MzcxfQ.tRsvQJX9MI7nKHnsvvjmsK3rXnEJm9JqLl_3ipNAreo"
    
    print("\n" + "="*70)
    print("  Verdent 账号深度对比测试")
    print("="*70)
    
    # 测试两个账号
    normal_results = test_account_capabilities(normal_token, "正常账号")
    abnormal_results = test_account_capabilities(abnormal_token, "异常账号")
    
    # 对比结果
    compare_capabilities(normal_results, abnormal_results)
    
    print("\n" + "="*70)
    print("  测试完成")
    print("="*70)


if __name__ == "__main__":
    main()
