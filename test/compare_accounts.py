import json
import datetime
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlencode


class VerdentAPI:
    def __init__(
        self,
        host: str = 'agent.verdent.ai',
        port: int = 443,
        login_host: str = 'login.verdent.ai',
        log_host: str = 'log.verdent.ai',
        token: Optional[str] = None,
        timeout: int = 10
    ):
        self.host = host
        self.port = port
        self.login_host = login_host
        self.log_host = log_host
        self.token = token
        self.timeout = timeout
        
        protocol = 'https' if port == 443 else 'http'
        port_suffix = '' if port in [443, 80] else f':{port}'
        self.base_url = f'{protocol}://{host}{port_suffix}'
        self.login_url = f'https://{login_host}'
        self.log_url = f'https://{log_host}'
        
        self.ws_protocol = 'wss' if port == 443 else 'ws'
        self.ws_url = f'{self.ws_protocol}://{host}{port_suffix}/chat'
    
    def set_token(self, token: str) -> None:
        self.token = token
    
    def get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.token:
            headers['Cookie'] = f'token={self.token}'
        return headers
    
    def fetch_user_info(self) -> Dict[str, Any]:
        try:
            url = f'{self.base_url}/user/center/info'
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', {})
        except Exception as e:
            print(f'Failed to fetch user info: {str(e)}')
            raise

def parse_jwt(token):
    """解析JWT token的payload部分"""
    import base64
    parts = token.split('.')
    if len(parts) != 3:
        return None
    
    payload = parts[1]
    # 添加padding
    padding = len(payload) % 4
    if padding:
        payload += '=' * (4 - padding)
    
    try:
        decoded = base64.b64decode(payload)
        return json.loads(decoded)
    except:
        return None

def timestamp_to_datetime(timestamp):
    """将时间戳转换为日期时间字符串"""
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def get_account_info(token, label):
    """获取账号的完整信息"""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print('='*60)
    
    # 解析JWT
    jwt_payload = parse_jwt(token)
    if jwt_payload:
        print("\n【JWT Token信息】")
        print(f"  用户ID: {jwt_payload.get('user_id', 'N/A')}")
        print(f"  Token类型: {jwt_payload.get('token_type', 'N/A')}")
        print(f"  版本: {jwt_payload.get('version', 'N/A')}")
        
        if 'iat' in jwt_payload:
            print(f"  签发时间: {timestamp_to_datetime(jwt_payload['iat'])}")
        if 'exp' in jwt_payload:
            print(f"  过期时间: {timestamp_to_datetime(jwt_payload['exp'])}")
        if 'nbf' in jwt_payload:
            print(f"  生效时间: {timestamp_to_datetime(jwt_payload['nbf'])}")
        
        # 计算有效期
        if 'exp' in jwt_payload and 'iat' in jwt_payload:
            duration_days = (jwt_payload['exp'] - jwt_payload['iat']) / (24 * 3600)
            print(f"  有效期: {duration_days:.1f} 天")
    
    # 使用API获取账号详细信息
    api = VerdentAPI(token=token)
    
    try:
        user_info = api.fetch_user_info()
        
        print("\n【账号基本信息】")
        print(f"  邮箱: {user_info.get('email', 'N/A')}")
        print(f"  用户名: {user_info.get('username', 'N/A')}")
        print(f"  用户类型: {user_info.get('userType', 'N/A')}")
        print(f"  账号状态: {user_info.get('status', 'N/A')}")
        
        # Token信息
        token_info = user_info.get('tokenInfo', {})
        if token_info:
            print("\n【积分信息】")
            print(f"  免费积分: {token_info.get('tokenFree', 0):,}")
            print(f"  已消耗积分: {token_info.get('tokenConsumed', 0):,}")
            print(f"  剩余积分: {token_info.get('tokenFree', 0) - token_info.get('tokenConsumed', 0):,}")
        
        # 订阅信息
        subscriptions = user_info.get('subscriptions', [])
        if subscriptions:
            print("\n【订阅信息】")
            for idx, sub in enumerate(subscriptions, 1):
                print(f"  订阅{idx}:")
                print(f"    - 计划ID: {sub.get('planId', 'N/A')}")
                print(f"    - 计划名称: {sub.get('planName', 'N/A')}")
                print(f"    - 状态: {sub.get('status', 'N/A')}")
                print(f"    - 类型: {sub.get('type', 'N/A')}")
                if 'startDate' in sub:
                    print(f"    - 开始时间: {sub['startDate']}")
                if 'endDate' in sub:
                    print(f"    - 结束时间: {sub['endDate']}")
        
        # 试用信息
        if 'isTrialAvailable' in user_info:
            print(f"\n【试用状态】")
            print(f"  试用可用: {user_info.get('isTrialAvailable', False)}")
            print(f"  试用计划ID: {user_info.get('trialPlanId', 'N/A')}")
        
        # 其他信息
        if 'createdAt' in user_info:
            print(f"\n【账号创建时间】")
            print(f"  {user_info['createdAt']}")
            
        return user_info
        
    except Exception as e:
        print(f"\n【错误】获取账号信息失败: {str(e)}")
        return None

def compare_accounts(info1, info2):
    """对比两个账号的差异"""
    print(f"\n{'='*60}")
    print("  账号对比分析")
    print('='*60)
    
    if not info1 or not info2:
        print("\n【警告】无法对比，至少有一个账号信息获取失败")
        return
    
    # 对比积分
    token1 = info1.get('tokenInfo', {})
    token2 = info2.get('tokenInfo', {})
    
    print("\n【积分对比】")
    print(f"  正常账号 - 免费积分: {token1.get('tokenFree', 0):,}, 已消耗: {token1.get('tokenConsumed', 0):,}")
    print(f"  异常账号 - 免费积分: {token2.get('tokenFree', 0):,}, 已消耗: {token2.get('tokenConsumed', 0):,}")
    
    # 对比账号状态
    print("\n【状态对比】")
    print(f"  正常账号状态: {info1.get('status', 'N/A')}")
    print(f"  异常账号状态: {info2.get('status', 'N/A')}")
    
    # 对比订阅
    subs1 = info1.get('subscriptions', [])
    subs2 = info2.get('subscriptions', [])
    
    print("\n【订阅对比】")
    print(f"  正常账号订阅数: {len(subs1)}")
    print(f"  异常账号订阅数: {len(subs2)}")
    
    # 对比试用状态
    print("\n【试用状态对比】")
    print(f"  正常账号试用可用: {info1.get('isTrialAvailable', 'N/A')}")
    print(f"  异常账号试用可用: {info2.get('isTrialAvailable', 'N/A')}")
    
    # 找出关键差异
    print("\n【关键差异】")
    differences = []
    
    if info1.get('status') != info2.get('status'):
        differences.append(f"账号状态不同: 正常账号[{info1.get('status')}] vs 异常账号[{info2.get('status')}]")
    
    if token1.get('tokenFree', 0) != token2.get('tokenFree', 0):
        differences.append(f"免费积分不同: 正常账号[{token1.get('tokenFree', 0)}] vs 异常账号[{token2.get('tokenFree', 0)}]")
    
    if len(subs1) != len(subs2):
        differences.append(f"订阅数量不同: 正常账号[{len(subs1)}个] vs 异常账号[{len(subs2)}个]")
    
    if info1.get('isTrialAvailable') != info2.get('isTrialAvailable'):
        differences.append(f"试用状态不同: 正常账号[{info1.get('isTrialAvailable')}] vs 异常账号[{info2.get('isTrialAvailable')}]")
    
    if differences:
        for diff in differences:
            print(f"  • {diff}")
    else:
        print("  没有发现明显差异")

def main():
    # 定义两个token
    normal_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjU2MTY0MzM4ODkyODAsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU4Nzc4OTIsImlhdCI6MTc2MzI4NTg5MiwibmJmIjoxNzYzMjg1ODkyfQ.xL1UUy032DzbW9vVgWKOkdvk0ZWZeQfKa0fPxIrqo-U"
    abnormal_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjMwNDA3ODU2NDU1NjgsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU3MjgzNzEsImlhdCI6MTc2MzEzNjM3MSwibmJmIjoxNzYzMTM2MzcxfQ.tRsvQJX9MI7nKHnsvvjmsK3rXnEJm9JqLl_3ipNAreo"
    
    # 获取账号信息
    normal_info = get_account_info(normal_token, "正常账号")
    abnormal_info = get_account_info(abnormal_token, "异常账号")
    
    # 对比账号
    compare_accounts(normal_info, abnormal_info)
    
    print("\n" + "="*60)
    print("  分析完成")
    print("="*60)

if __name__ == "__main__":
    main()
