import os
import json
import sys
import argparse
import datetime
from typing import Dict, List, Optional, Any
import win32cred
import win32security
import win32con
import win32api
import win32crypt


class CredentialManager:
    """Windows凭证管理器操作类"""
    
    def __init__(self):
        self.cred_type_mapping = {
            "generic": win32cred.CRED_TYPE_GENERIC,
            "domain_password": win32cred.CRED_TYPE_DOMAIN_PASSWORD,
            "domain_certificate": win32cred.CRED_TYPE_DOMAIN_CERTIFICATE,
            "domain_visible": win32cred.CRED_TYPE_DOMAIN_VISIBLE_PASSWORD,
            "generic_certificate": win32cred.CRED_TYPE_GENERIC_CERTIFICATE,
            "domain_extended": win32cred.CRED_TYPE_DOMAIN_EXTENDED
        }
    
    def list_credentials(self) -> List[Dict[str, Any]]:
        """列出所有凭证"""
        try:
            creds = win32cred.CredEnumerate()
            cred_list = []
            
            for cred in creds:
                cred_info = {
                    "filename": cred.get("Flags", ""),
                    "version": "Vista/7/8/10",
                    "decrypted_size": len(cred.get("CredentialBlob", b"")),
                    "modified_time": self._format_filetime(cred.get("LastWritten", 0)),
                    "entry_type": self._get_cred_type_name(cred.get("Type", 0)),
                    "persist": self._get_persist_name(cred.get("Persist", 0)),
                    "entry_name": cred.get("TargetName", ""),
                    "user_name": cred.get("UserName", ""),
                    "password": self._decrypt_password(cred.get("CredentialBlob", b"")),
                    "full_path": self._get_full_path(cred),
                    "file_size": len(str(cred)),
                    "file_modified_time": self._format_filetime(cred.get("LastWritten", 0)),
                    "file_created_time": self._format_filetime(cred.get("LastWritten", 0))
                }
                cred_list.append(cred_info)
            
            return cred_list
        except Exception as e:
            print(f"列出凭证时出错: {str(e)}")
            return []
    
    def get_credential(self, target_name: str, cred_type: str = "generic") -> Optional[Dict[str, Any]]:
        """获取特定凭证"""
        try:
            type_value = self.cred_type_mapping.get(cred_type.lower(), win32cred.CRED_TYPE_GENERIC)
            cred = win32cred.CredRead(
                TargetName=target_name,
                Type=type_value
            )
            
            cred_info = {
                "filename": cred.get("Flags", ""),
                "version": "Vista/7/8/10",
                "decrypted_size": len(cred.get("CredentialBlob", b"")),
                "modified_time": self._format_filetime(cred.get("LastWritten", 0)),
                "entry_type": self._get_cred_type_name(cred.get("Type", 0)),
                "persist": self._get_persist_name(cred.get("Persist", 0)),
                "entry_name": cred.get("TargetName", ""),
                "user_name": cred.get("UserName", ""),
                "password": self._decrypt_password(cred.get("CredentialBlob", b"")),
                "full_path": self._get_full_path(cred),
                "file_size": len(str(cred)),
                "file_modified_time": self._format_filetime(cred.get("LastWritten", 0)),
                "file_created_time": self._format_filetime(cred.get("LastWritten", 0))
            }
            
            return cred_info
        except Exception as e:
            print(f"获取凭证时出错: {str(e)}")
            return None
    
    def update_credential(self, target_name: str, username: str, password: str, 
                          cred_type: str = "generic", persist: str = "enterprise") -> bool:
        """更新凭证"""
        try:
            # 获取现有凭证信息（如果存在）
            type_value = self.cred_type_mapping.get(cred_type.lower(), win32cred.CRED_TYPE_GENERIC)
            persist_value = self._get_persist_value(persist)
            
            # 确保密码是字符串类型
            if isinstance(password, bytes):
                password_str = password.decode('utf-8')
            else:
                password_str = str(password)
            
            # 确保CredentialBlob是字节类型（Windows要求）
            if isinstance(password_str, str):
                credential_blob = password_str.encode('utf-16le')
            else:
                credential_blob = str(password_str).encode('utf-16le')
            
            # 准备凭证信息
            credential = {
                "Flags": 0,
                "Type": type_value,
                "TargetName": target_name,
                "UserName": username,
                "CredentialBlob": credential_blob,
                "Persist": persist_value
            }
            
            # 尝试更新现有凭证
            try:
                win32cred.CredWrite(credential, 0)
                return True
            except Exception as write_error:
                print(f"写入凭证时出错: {str(write_error)}")
                return False
                
        except Exception as e:
            print(f"更新凭证时出错: {str(e)}")
            return False
    
    def delete_credential(self, target_name: str, cred_type: str = "generic") -> bool:
        """删除凭证"""
        try:
            type_value = self.cred_type_mapping.get(cred_type.lower(), win32cred.CRED_TYPE_GENERIC)
            win32cred.CredDelete(
                TargetName=target_name,
                Type=type_value
            )
            print(f"凭证 '{target_name}' 已成功删除")
            return True
        except Exception as e:
            print(f"删除凭证时出错: {str(e)}")
            return False
    
    def create_credential(self, target_name: str, username: str, password: str, 
                          cred_type: str = "generic", persist: str = "enterprise") -> bool:
        """创建新凭证"""
        try:
            type_value = self.cred_type_mapping.get(cred_type.lower(), win32cred.CRED_TYPE_GENERIC)
            persist_value = self._get_persist_value(persist)
            
            # 确保密码是字符串类型
            if isinstance(password, bytes):
                password_str = password.decode('utf-8')
            else:
                password_str = str(password)
            
            # 确保CredentialBlob是字节类型（Windows要求）
            if isinstance(password_str, str):
                credential_blob = password_str.encode('utf-16le')
            else:
                credential_blob = str(password_str).encode('utf-16le')
            
            # 准备凭证信息
            credential = {
                "Flags": 0,
                "Type": type_value,
                "TargetName": target_name,
                "UserName": username,
                "CredentialBlob": credential_blob,
                "Persist": persist_value
            }
            
            win32cred.CredWrite(credential, 0)
            return True
        except Exception as e:
            print(f"创建凭证时出错: {str(e)}")
            return False
    
    def _get_cred_type_name(self, cred_type: int) -> str:
        """获取凭证类型名称"""
        type_names = {
            win32cred.CRED_TYPE_GENERIC: "Generic",
            win32cred.CRED_TYPE_DOMAIN_PASSWORD: "Domain Password",
            win32cred.CRED_TYPE_DOMAIN_CERTIFICATE: "Domain Certificate",
            win32cred.CRED_TYPE_DOMAIN_VISIBLE_PASSWORD: "Domain Visible Password",
            win32cred.CRED_TYPE_GENERIC_CERTIFICATE: "Generic Certificate",
            win32cred.CRED_TYPE_DOMAIN_EXTENDED: "Domain Extended"
        }
        return type_names.get(cred_type, "Unknown")
    
    def _get_persist_name(self, persist: int) -> str:
        """获取持久性名称"""
        persist_names = {
            win32cred.CRED_PERSIST_SESSION: "Session",
            win32cred.CRED_PERSIST_LOCAL_MACHINE: "Local Machine",
            win32cred.CRED_PERSIST_ENTERPRISE: "Enterprise"
        }
        return persist_names.get(persist, "Unknown")
    
    def _get_persist_value(self, persist_name: str) -> int:
        """根据名称获取持久性值"""
        persist_values = {
            "session": win32cred.CRED_PERSIST_SESSION,
            "local": win32cred.CRED_PERSIST_LOCAL_MACHINE,
            "enterprise": win32cred.CRED_PERSIST_ENTERPRISE
        }
        return persist_values.get(persist_name.lower(), win32cred.CRED_PERSIST_ENTERPRISE)
    
    def _format_filetime(self, filetime: int) -> str:
        """格式化文件时间"""
        try:
            if filetime == 0:
                return "未知"
            
            # 转换为datetime对象
            dt = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=filetime/10)
            return dt.strftime("%Y/%m/%d %H:%M:%S")
        except:
            return "未知"
    
    def _decrypt_password(self, blob: bytes) -> str:
        """解密密码"""
        try:
            if not blob:
                return ""
            
            # 尝试直接解码为UTF-16LE（Windows凭证存储格式）
            try:
                decoded = blob.decode('utf-16le').rstrip('\x00')
                # 如果解码结果是JSON格式，尝试格式化输出
                if decoded.startswith('{') and decoded.endswith('}'):
                    try:
                        json_data = json.loads(decoded)
                        return json.dumps(json_data, indent=2, ensure_ascii=False)
                    except:
                        return decoded
                return decoded
            except UnicodeDecodeError:
                # 如果UTF-16LE解码失败，尝试UTF-8
                try:
                    return blob.decode('utf-8').rstrip('\x00')
                except UnicodeDecodeError:
                    # 如果都失败，返回十六进制表示
                    return blob.hex()
            except:
                # 如果直接解码失败，尝试其他方法
                return str(blob)
        except Exception as e:
            print(f"解密密码时出错: {str(e)}")
            return f"<无法解密: {len(blob) if blob else 0} 字节>"
    
    def _get_full_path(self, cred: Dict[str, Any]) -> str:
        """获取凭证的完整路径"""
        try:
            # 这里我们构建一个模拟的路径，因为实际的Windows凭证路径可能不易获取
            username = win32api.GetUserName()
            target = cred.get("TargetName", "")
            return f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Credentials\\{target}"
        except:
            return "未知路径"


class CredentialChanger:
    """凭证更改器主类"""
    
    def __init__(self):
        self.cred_manager = CredentialManager()
    
    def list_all_credentials(self, output_format: str = "table") -> None:
        """列出所有凭证"""
        credentials = self.cred_manager.list_credentials()
        
        if not credentials:
            print("没有找到凭证")
            return
        
        if output_format.lower() == "json":
            print(json.dumps(credentials, indent=2, ensure_ascii=False))
        else:
            # 表格格式输出
            print(f"{'Filename':<40} {'Version':<15} {'Decrypted Size':<15} {'Modified Time':<20} {'Entry Type':<20} {'Persist':<12} {'Entry Name':<40} {'User Name':<30}")
            print("-" * 192)
            
            for cred in credentials:
                filename = cred.get("filename", "") or ""
                version = cred.get("version", "") or ""
                size = cred.get("decrypted_size", 0)
                modified = cred.get("modified_time", "") or ""
                entry_type = cred.get("entry_type", "") or ""
                persist = cred.get("persist", "") or ""
                entry_name = cred.get("entry_name", "") or ""
                username = cred.get("user_name", "") or ""
                
                print(f"{filename:<40} {version:<15} {size:<15} {modified:<20} {entry_type:<20} {persist:<12} {entry_name:<40} {username:<30}")
    
    def get_credential_info(self, target_name: str, cred_type: str = "generic") -> None:
        """获取特定凭证信息"""
        cred = self.cred_manager.get_credential(target_name, cred_type)
        
        if not cred:
            print(f"未找到凭证: {target_name}")
            return
        
        print(f"凭证详细信息:")
        print(f"  文件名: {cred.get('filename', '')}")
        print(f"  版本: {cred.get('version', '')}")
        print(f"  解密大小: {cred.get('decrypted_size', 0)}")
        print(f"  修改时间: {cred.get('modified_time', '')}")
        print(f"  条目类型: {cred.get('entry_type', '')}")
        print(f"  持久性: {cred.get('persist', '')}")
        print(f"  条目名称: {cred.get('entry_name', '')}")
        print(f"  用户名: {cred.get('user_name', '')}")
        print(f"  密码: {cred.get('password', '')}")
        print(f"  完整路径: {cred.get('full_path', '')}")
    
    def update_access_token(self, target_name: str, new_token: str, expire_at: Optional[int] = None) -> None:
        """更新访问令牌"""
        try:
            # 解析现有凭证以获取用户名
            existing_cred = self.cred_manager.get_credential(target_name)
            username = "access-token"  # 默认用户名
            
            if existing_cred:
                # 确保用户名是字符串类型
                user_name = existing_cred.get("user_name", "")
                if isinstance(user_name, bytes):
                    try:
                        username = user_name.decode('utf-8')
                    except:
                        username = "access-token"
                elif user_name:
                    username = str(user_name)
            
            # 准备新的令牌数据
            if expire_at:
                token_data = {
                    "accessToken": new_token,
                    "expireAt": expire_at
                }
            else:
                # 如果没有提供过期时间，尝试从现有令牌中获取或设置默认值
                token_data = {
                    "accessToken": new_token,
                    "expireAt": int(datetime.datetime.now().timestamp() * 1000) + 86400000  # 默认24小时后过期
                }
            
            # 将令牌数据转换为JSON字符串
            password_json = json.dumps(token_data)
            
            # 更新凭证
            success = self.cred_manager.update_credential(
                target_name=target_name,
                username=username,
                password=password_json,
                cred_type="generic",
                persist="enterprise"
            )
            
            if success:
                # 验证更新是否成功
                updated_cred = self.cred_manager.get_credential(target_name)
                if updated_cred:
                    password = updated_cred.get("password", "")
                    if new_token in password:
                        print(f"访问令牌 '{target_name}' 已成功更新")
                        if expire_at:
                            expire_dt = datetime.datetime.fromtimestamp(expire_at / 1000)
                            print(f"过期时间: {expire_dt.strftime('%Y/%m/%d %H:%M:%S')}")
                    else:
                        print(f"令牌更新可能未成功，无法在凭证中找到新令牌")
                else:
                    print(f"令牌更新后无法验证结果")
            else:
                print(f"令牌更新失败")
        except Exception as e:
            print(f"更新访问令牌时出错: {str(e)}")
    
    def create_access_token(self, target_name: str, token: str, expire_at: Optional[int] = None) -> None:
        """创建新的访问令牌凭证"""
        try:
            # 准备令牌数据
            if expire_at:
                token_data = {
                    "accessToken": token,
                    "expireAt": expire_at
                }
            else:
                # 默认24小时后过期
                token_data = {
                    "accessToken": token,
                    "expireAt": int(datetime.datetime.now().timestamp() * 1000) + 86400000
                }
            
            # 将令牌数据转换为JSON字符串
            password_json = json.dumps(token_data)
            
            # 创建凭证
            success = self.cred_manager.create_credential(
                target_name=target_name,
                username="access-token",
                password=password_json,
                cred_type="generic",
                persist="enterprise"
            )
            
            if success:
                print(f"访问令牌 '{target_name}' 已成功创建")
                if expire_at:
                    expire_dt = datetime.datetime.fromtimestamp(expire_at / 1000)
                    print(f"过期时间: {expire_dt.strftime('%Y/%m/%d %H:%M:%S')}")
        except Exception as e:
            print(f"创建访问令牌时出错: {str(e)}")
    
    def delete_credential(self, target_name: str, cred_type: str = "generic") -> None:
        """删除凭证"""
        success = self.cred_manager.delete_credential(target_name, cred_type)
        if not success:
            print(f"删除凭证 '{target_name}' 失败")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Windows凭证更改器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 列出所有凭证
    list_parser = subparsers.add_parser("list", help="列出所有凭证")
    list_parser.add_argument("--format", choices=["table", "json"], default="table", help="输出格式")
    
    # 获取凭证信息
    get_parser = subparsers.add_parser("get", help="获取特定凭证信息")
    get_parser.add_argument("target", help="凭证目标名称")
    get_parser.add_argument("--type", choices=["generic", "domain_password", "domain_certificate", 
                                              "domain_visible", "generic_certificate", "domain_extended"],
                           default="generic", help="凭证类型")
    
    # 更新凭证
    update_parser = subparsers.add_parser("update", help="更新凭证")
    update_parser.add_argument("target", help="凭证目标名称")
    update_parser.add_argument("username", help="用户名")
    update_parser.add_argument("password", help="密码")
    update_parser.add_argument("--type", choices=["generic", "domain_password", "domain_certificate", 
                                                "domain_visible", "generic_certificate", "domain_extended"],
                             default="generic", help="凭证类型")
    update_parser.add_argument("--persist", choices=["session", "local", "enterprise"],
                             default="enterprise", help="持久性")
    
    # 创建凭证
    create_parser = subparsers.add_parser("create", help="创建新凭证")
    create_parser.add_argument("target", help="凭证目标名称")
    create_parser.add_argument("username", help="用户名")
    create_parser.add_argument("password", help="密码")
    create_parser.add_argument("--type", choices=["generic", "domain_password", "domain_certificate", 
                                                "domain_visible", "generic_certificate", "domain_extended"],
                             default="generic", help="凭证类型")
    create_parser.add_argument("--persist", choices=["session", "local", "enterprise"],
                             default="enterprise", help="持久性")
    
    # 删除凭证
    delete_parser = subparsers.add_parser("delete", help="删除凭证")
    delete_parser.add_argument("target", help="凭证目标名称")
    delete_parser.add_argument("--type", choices=["generic", "domain_password", "domain_certificate", 
                                                "domain_visible", "generic_certificate", "domain_extended"],
                             default="generic", help="凭证类型")
    
    # 更新访问令牌
    token_update_parser = subparsers.add_parser("update-token", help="更新访问令牌")
    token_update_parser.add_argument("target", help="令牌目标名称")
    token_update_parser.add_argument("token", help="新的访问令牌")
    token_update_parser.add_argument("--expire", type=int, help="过期时间(毫秒时间戳)")
    
    # 创建访问令牌
    token_create_parser = subparsers.add_parser("create-token", help="创建访问令牌")
    token_create_parser.add_argument("target", help="令牌目标名称")
    token_create_parser.add_argument("token", help="访问令牌")
    token_create_parser.add_argument("--expire", type=int, help="过期时间(毫秒时间戳)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    changer = CredentialChanger()
    
    try:
        if args.command == "list":
            changer.list_all_credentials(args.format)
        elif args.command == "get":
            changer.get_credential_info(args.target, args.type)
        elif args.command == "update":
            changer.cred_manager.update_credential(args.target, args.username, args.password, args.type, args.persist)
        elif args.command == "create":
            changer.cred_manager.create_credential(args.target, args.username, args.password, args.type, args.persist)
        elif args.command == "delete":
            changer.delete_credential(args.target, args.type)
        elif args.command == "update-token":
            changer.update_access_token(args.target, args.token, args.expire)
        elif args.command == "create-token":
            changer.create_access_token(args.target, args.token, args.expire)
    except Exception as e:
        print(f"执行命令时出错: {str(e)}")


if __name__ == "__main__":
    main()