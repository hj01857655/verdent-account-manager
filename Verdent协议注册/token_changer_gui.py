#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import ctypes
from ctypes import wintypes
import subprocess
import winreg
import uuid
import time
import psutil


class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", wintypes.LPBYTE),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


PCREDENTIAL = ctypes.POINTER(CREDENTIAL)
CRED_TYPE_GENERIC = 1
CRED_PERSIST_ENTERPRISE = 3


def read_credential_utf8(target_name):
    """使用ctypes读取凭证"""
    advapi32 = ctypes.windll.advapi32
    
    pcred = PCREDENTIAL()
    result = advapi32.CredReadW(target_name, CRED_TYPE_GENERIC, 0, ctypes.byref(pcred))
    
    if not result:
        error_code = ctypes.get_last_error()
        raise ctypes.WinError(error_code)
    
    try:
        cred = pcred.contents
        
        # 读取凭证信息
        username = cred.UserName if cred.UserName else ""
        
        # 读取密码（UTF-8字节）
        blob_size = cred.CredentialBlobSize
        blob_bytes = ctypes.string_at(cred.CredentialBlob, blob_size)
        
        # 尝试解码为UTF-8
        try:
            password = blob_bytes.decode('utf-8')
        except UnicodeDecodeError:
            password = blob_bytes.decode('utf-16le').replace('\x00', '')
        
        # 转换FILETIME到datetime
        filetime = (cred.LastWritten.dwHighDateTime << 32) + cred.LastWritten.dwLowDateTime
        if filetime > 0:
            dt = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=filetime/10)
            modified_time = dt.strftime("%Y/%m/%d %H:%M:%S")
        else:
            modified_time = "未知"
        
        return {
            "user_name": username,
            "password": password,
            "modified_time": modified_time
        }
    finally:
        advapi32.CredFree(pcred)


def write_credential_utf8(target_name, username, password_json):
    """使用ctypes直接写入UTF-8格式的凭证"""
    advapi32 = ctypes.windll.advapi32
    
    # 将JSON密码编码为UTF-8字节
    password_bytes = password_json.encode('utf-8')
    
    # 创建CREDENTIAL结构
    cred = CREDENTIAL()
    cred.Flags = 0
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = target_name
    cred.Comment = None
    cred.CredentialBlobSize = len(password_bytes)
    cred.CredentialBlob = ctypes.cast(
        ctypes.create_string_buffer(password_bytes),
        wintypes.LPBYTE
    )
    cred.Persist = CRED_PERSIST_ENTERPRISE
    cred.AttributeCount = 0
    cred.Attributes = None
    cred.TargetAlias = None
    cred.UserName = username
    
    # 调用CredWriteW
    result = advapi32.CredWriteW(ctypes.byref(cred), 0)
    
    if not result:
        error_code = ctypes.get_last_error()
        raise ctypes.WinError(error_code)
    
    return True


class VerdentManager:
    """管理Verdent软件和系统注册表"""
    
    def __init__(self):
        self.registry_key = r"SOFTWARE\Microsoft\Cryptography"
        self.value_name = "MachineGuid"
        self.backup_file = "machine_guid_backup.json"
        self.verdent_process_name = "Verdent.exe"
        
    def backup_machine_guid(self):
        """备份原始MachineGuid"""
        try:
            # 读取当前的MachineGuid
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.registry_key, 0, winreg.KEY_READ) as key:
                current_guid, _ = winreg.QueryValueEx(key, self.value_name)
                
            # 保存到备份文件
            backup_data = {
                "original_machine_guid": current_guid,
                "backup_time": datetime.datetime.now().isoformat(),
                "modified_guids": []
            }
            
            # 如果备份文件已存在，读取并更新
            if os.path.exists(self.backup_file):
                try:
                    with open(self.backup_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        # 只保留原始GUID不变
                        if "original_machine_guid" in existing_data:
                            backup_data["original_machine_guid"] = existing_data["original_machine_guid"]
                        if "modified_guids" in existing_data:
                            backup_data["modified_guids"] = existing_data["modified_guids"]
                except:
                    pass
            
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return current_guid
        except Exception as e:
            raise Exception(f"备份MachineGuid失败: {e}")
    
    def change_machine_guid(self, new_guid=None):
        """修改MachineGuid为新的随机值"""
        try:
            # 生成新的GUID
            if new_guid is None:
                new_guid = str(uuid.uuid4())
            
            # 备份当前值
            current_guid = self.backup_machine_guid()
            
            # 修改注册表（需要管理员权限）
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.registry_key, 0, 
                              winreg.KEY_WRITE | winreg.KEY_READ) as key:
                winreg.SetValueEx(key, self.value_name, 0, winreg.REG_SZ, new_guid)
            
            # 更新备份文件，记录修改历史
            if os.path.exists(self.backup_file):
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                backup_data["modified_guids"].append({
                    "guid": new_guid,
                    "modified_time": datetime.datetime.now().isoformat(),
                    "previous_guid": current_guid
                })
                
                with open(self.backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return new_guid
        except PermissionError:
            raise Exception("需要管理员权限才能修改注册表。请以管理员身份运行程序。")
        except Exception as e:
            raise Exception(f"修改MachineGuid失败: {e}")
    
    def restore_machine_guid(self):
        """还原到原始的MachineGuid"""
        try:
            if not os.path.exists(self.backup_file):
                raise Exception("未找到备份文件，无法还原")
            
            with open(self.backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            if "original_machine_guid" not in backup_data:
                raise Exception("备份文件中未找到原始MachineGuid")
            
            original_guid = backup_data["original_machine_guid"]
            
            # 还原注册表
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.registry_key, 0, 
                              winreg.KEY_WRITE | winreg.KEY_READ) as key:
                winreg.SetValueEx(key, self.value_name, 0, winreg.REG_SZ, original_guid)
            
            return original_guid
        except PermissionError:
            raise Exception("需要管理员权限才能修改注册表。请以管理员身份运行程序。")
        except Exception as e:
            raise Exception(f"还原MachineGuid失败: {e}")
    
    def get_current_machine_guid(self):
        """获取当前的MachineGuid"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.registry_key, 0, winreg.KEY_READ) as key:
                current_guid, _ = winreg.QueryValueEx(key, self.value_name)
                return current_guid
        except Exception as e:
            raise Exception(f"读取MachineGuid失败: {e}")
    
    def kill_verdent_process(self):
        """终止Verdent进程"""
        killed_count = 0
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == self.verdent_process_name:
                    try:
                        proc.kill()
                        killed_count += 1
                    except:
                        pass
        except:
            # 如果psutil失败，使用taskkill命令
            try:
                subprocess.run(["taskkill", "/F", "/IM", self.verdent_process_name], 
                             capture_output=True, text=True, shell=True)
                killed_count = 1
            except:
                pass
        return killed_count
    
    def start_verdent(self):
        """启动Verdent软件"""
        try:
            # 首先检查是否有保存的路径
            saved_path = self.load_verdent_path()
            if saved_path and os.path.exists(saved_path):
                subprocess.Popen([saved_path], shell=False)
                return True
            
            # 尝试常见的安装路径
            possible_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\verdent\Verdent.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\verdent-deck\Verdent.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\Verdent\Verdent.exe"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%\Verdent\Verdent.exe"),
                # 添加更多可能的路径
                os.path.expandvars(r"%APPDATA%\Verdent\Verdent.exe"),
                os.path.expandvars(r"C:\Program Files\Verdent\Verdent.exe"),
                os.path.expandvars(r"C:\Program Files (x86)\Verdent\Verdent.exe"),
            ]
            
            # 首先检查快捷方式
            shortcut_paths = [
                os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Verdent.lnk"),
                os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Verdent.lnk"),
                os.path.expandvars(r"%USERPROFILE%\Desktop\Verdent.lnk"),
            ]
            
            # 尝试通过快捷方式启动
            for shortcut in shortcut_paths:
                if os.path.exists(shortcut):
                    os.startfile(shortcut)
                    return True
            
            # 尝试直接启动exe文件
            for path in possible_paths:
                if os.path.exists(path):
                    subprocess.Popen([path], shell=False)
                    return True
            
            # 如果都找不到，返回False而不是尝试错误的命令
            return False
        except Exception as e:
            return False
    
    def restart_verdent(self, delay=3):
        """重启Verdent软件"""
        # 终止进程
        killed = self.kill_verdent_process()
        if killed > 0:
            time.sleep(delay)  # 等待进程完全终止
        
        # 启动软件
        started = self.start_verdent()
        if not started:
            # 如果自动启动失败，提示用户手动查找
            return self.browse_for_verdent()
        return started
    
    def browse_for_verdent(self):
        """让用户手动选择Verdent的安装位置"""
        try:
            import tkinter.filedialog as filedialog
            
            # 提示用户选择Verdent.exe
            file_path = filedialog.askopenfilename(
                title="请选择 Verdent.exe 文件",
                filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
                initialdir=os.path.expandvars(r"%LOCALAPPDATA%\Programs")
            )
            
            if file_path and os.path.exists(file_path):
                # 保存路径供下次使用
                self.save_verdent_path(file_path)
                # 启动程序
                subprocess.Popen([file_path], shell=False)
                return True
            return False
        except Exception:
            return False
    
    def save_verdent_path(self, path):
        """保存Verdent路径到配置文件"""
        try:
            config = {
                "verdent_path": path,
                "last_updated": datetime.datetime.now().isoformat()
            }
            with open("verdent_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def load_verdent_path(self):
        """从配置文件加载Verdent路径"""
        try:
            if os.path.exists("verdent_config.json"):
                with open("verdent_config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("verdent_path")
        except:
            pass
        return None


class TokenChangerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Verdent Access Token 更改器 (增强版)")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 兼容新旧两种命名
        self.target_names = [
            "LegacyGeneric:target=ai.verdent.deck/access-token"  # 旧名称（兼容已存在的凭证）
        ]
        self.target_name = self.target_names[0]  # 默认使用旧名称以保持兼容
        self.verdent_manager = VerdentManager()
        self.init_status = "准备就绪"
        self.current_machine_guid = None
        self.is_admin = False
        
        # 先创建界面
        self._create_widgets()
        
        # 启动时的初始化操作
        self._initialize_system()
        
        # 加载当前Token
        self._load_current_token()
        
        # 显示当前机器码
        self._display_machine_guid()
    
    def _initialize_system(self):
        """初始化系统：检查管理员权限、修改MachineGuid"""
        try:
            # 检查是否以管理员权限运行
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                result = messagebox.askyesno(
                    "需要管理员权限",
                    "此程序需要管理员权限才能修改系统注册表。\n\n是否现在以管理员身份重新启动程序？"
                )
                if result:
                    # 以管理员权限重新启动
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable, " ".join(sys.argv), None, 1
                    )
                    sys.exit(0)
                else:
                    # 在主界面显示状态而不是弹窗
                    self.init_status = "未获得管理员权限，部分功能受限"
                    self.is_admin = False
                    return
            
            self.is_admin = True
            
            # 在后台执行初始化
            def init_task():
                try:
                    # 获取当前机器码
                    current_guid = self.verdent_manager.get_current_machine_guid()
                    self.init_status = f"当前机器码: {current_guid[:20]}..."
                    
                    # 生成新的机器码
                    new_guid = str(uuid.uuid4())
                    self.verdent_manager.change_machine_guid(new_guid)
                    
                    self.init_status = f"机器码已更改: {new_guid[:20]}..."
                    self.current_machine_guid = new_guid
                    
                except Exception as e:
                    self.init_status = f"初始化失败: {str(e)}"
            
            # 在新线程中执行初始化
            threading.Thread(target=init_task, daemon=True).start()
            
        except Exception as e:
            self.init_status = f"初始化错误: {str(e)}"
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(main_frame, text="Verdent Access Token 管理器", 
                                font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        info_frame = ttk.LabelFrame(main_frame, text="当前凭证信息", padding="10")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="目标名称:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.target_label = ttk.Label(info_frame, text=self.target_name, foreground="blue")
        self.target_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="用户名:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.username_label = ttk.Label(info_frame, text="加载中...")
        self.username_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="过期时间:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.expire_label = ttk.Label(info_frame, text="加载中...")
        self.expire_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="修改时间:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.modified_label = ttk.Label(info_frame, text="加载中...")
        self.modified_label.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        current_token_frame = ttk.LabelFrame(main_frame, text="当前 Access Token", padding="10")
        current_token_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        current_token_frame.columnconfigure(0, weight=1)
        current_token_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        self.current_token_text = scrolledtext.ScrolledText(current_token_frame, height=6, 
                                                             wrap=tk.WORD, font=("Consolas", 9))
        self.current_token_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.current_token_text.config(state=tk.DISABLED)
        
        new_token_frame = ttk.LabelFrame(main_frame, text="新 Access Token", padding="10")
        new_token_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        new_token_frame.columnconfigure(0, weight=1)
        new_token_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        self.new_token_text = scrolledtext.ScrolledText(new_token_frame, height=6, 
                                                        wrap=tk.WORD, font=("Consolas", 9))
        self.new_token_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        expire_frame = ttk.Frame(main_frame)
        expire_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        expire_frame.columnconfigure(1, weight=1)
        
        ttk.Label(expire_frame, text="过期时间 (小时):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.expire_hours = ttk.Spinbox(expire_frame, from_=1, to=8760, width=10)
        self.expire_hours.set(720)
        self.expire_hours.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(expire_frame, text="从现在起计算的小时数 (默认 720 小时 = 30 天)").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, pady=(0, 10))
        
        self.update_button = ttk.Button(button_frame, text="更新 Token", command=self._update_token)
        self.update_button.grid(row=0, column=0, padx=5)
        
        self.refresh_button = ttk.Button(button_frame, text="刷新信息", command=self._load_current_token)
        self.refresh_button.grid(row=0, column=1, padx=5)
        
        self.copy_button = ttk.Button(button_frame, text="复制当前 Token", command=self._copy_current_token)
        self.copy_button.grid(row=0, column=2, padx=5)
        
        # 添加系统管理按钮
        system_frame = ttk.LabelFrame(main_frame, text="系统管理", padding="10")
        system_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        system_frame.columnconfigure(0, weight=1)
        
        system_button_frame = ttk.Frame(system_frame)
        system_button_frame.pack()
        
        self.restart_button = ttk.Button(system_button_frame, text="重启 Verdent", 
                                        command=self._restart_verdent)
        self.restart_button.grid(row=0, column=0, padx=5)
        
        self.change_guid_button = ttk.Button(system_button_frame, text="更换机器码", 
                                            command=self._change_machine_guid)
        self.change_guid_button.grid(row=0, column=1, padx=5)
        
        self.restore_guid_button = ttk.Button(system_button_frame, text="还原机器码", 
                                             command=self._restore_machine_guid)
        self.restore_guid_button.grid(row=0, column=2, padx=5)
        
        self.view_guid_button = ttk.Button(system_button_frame, text="查看机器码", 
                                          command=self._view_machine_guid)
        self.view_guid_button.grid(row=0, column=3, padx=5)
        
        # 机器码显示区域
        guid_display_frame = ttk.Frame(system_frame)
        guid_display_frame.pack(pady=(10, 0), fill=tk.X)
        
        # 当前机器码
        ttk.Label(guid_display_frame, text="当前机器码:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.guid_label = ttk.Label(guid_display_frame, text="加载中...", font=("Consolas", 9))
        self.guid_label.pack(anchor=tk.W, padx=(20, 0))
        
        # 原始机器码
        ttk.Label(guid_display_frame, text="原始机器码:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 0))
        self.original_guid_label = ttk.Label(guid_display_frame, text="加载中...", font=("Consolas", 9))
        self.original_guid_label.pack(anchor=tk.W, padx=(20, 0))
        
        # 初始化状态
        ttk.Label(guid_display_frame, text="系统状态:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 0))
        self.init_status_label = ttk.Label(guid_display_frame, text="准备就绪", font=("Arial", 9))
        self.init_status_label.pack(anchor=tk.W, padx=(20, 0))
        
        self.status_label = ttk.Label(main_frame, text="准备就绪", foreground="green")
        self.status_label.grid(row=7, column=0)
    
    def _load_current_token(self):
        self._set_status("正在加载凭证信息...", "blue")
        self._disable_buttons()
        
        def load_task():
            try:
                cred = None
                last_error = None
                
                # 尝试读取凭证，兼容新旧名称
                for target_name in self.target_names:
                    try:
                        cred = read_credential_utf8(target_name)
                        self.target_name = target_name  # 记住成功的名称
                        break
                    except Exception as e:
                        last_error = e
                        continue
                
                if not cred and last_error:
                    raise last_error
                
                if cred:
                    self.root.after(0, lambda: self._update_ui_with_credential(cred))
                else:
                    self.root.after(0, lambda: self._set_status("未找到凭证", "red"))
                    self.root.after(0, self._enable_buttons)
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"加载失败: {str(e)}", "red"))
                self.root.after(0, self._enable_buttons)
        
        threading.Thread(target=load_task, daemon=True).start()
    
    def _update_ui_with_credential(self, cred):
        self.username_label.config(text=cred.get("user_name", "未知"))
        self.modified_label.config(text=cred.get("modified_time", "未知"))
        
        password_str = cred.get("password", "")
        
        # 移除空字节（\x00）
        password_str = password_str.replace('\x00', '')
        
        if isinstance(password_str, str) and password_str.startswith("{"):
            password_str = password_str.strip()
        
        try:
            if password_str and "{" in password_str:
                start_idx = password_str.find("{")
                end_idx = password_str.rfind("}") + 1
                json_str = password_str[start_idx:end_idx]
                
                token_data = json.loads(json_str)
                access_token = token_data.get("accessToken", "")
                expire_at = token_data.get("expireAt", 0)
                
                self.current_token_text.config(state=tk.NORMAL)
                self.current_token_text.delete(1.0, tk.END)
                self.current_token_text.insert(1.0, access_token)
                self.current_token_text.config(state=tk.DISABLED)
                
                if expire_at:
                    expire_dt = datetime.datetime.fromtimestamp(expire_at / 1000)
                    expire_str = expire_dt.strftime("%Y/%m/%d %H:%M:%S")
                    now = datetime.datetime.now()
                    if expire_dt > now:
                        remaining = expire_dt - now
                        days = remaining.days
                        hours = remaining.seconds // 3600
                        expire_str += f" (剩余 {days} 天 {hours} 小时)"
                        self.expire_label.config(text=expire_str, foreground="green")
                    else:
                        expire_str += " (已过期)"
                        self.expire_label.config(text=expire_str, foreground="red")
                else:
                    self.expire_label.config(text="未知", foreground="gray")
            else:
                self.current_token_text.config(state=tk.NORMAL)
                self.current_token_text.delete(1.0, tk.END)
                self.current_token_text.insert(1.0, password_str)
                self.current_token_text.config(state=tk.DISABLED)
                self.expire_label.config(text="未知", foreground="gray")
        except json.JSONDecodeError:
            self.current_token_text.config(state=tk.NORMAL)
            self.current_token_text.delete(1.0, tk.END)
            self.current_token_text.insert(1.0, password_str)
            self.current_token_text.config(state=tk.DISABLED)
            self.expire_label.config(text="未知", foreground="gray")
        except Exception as e:
            self.expire_label.config(text=f"解析错误: {str(e)}", foreground="red")
        
        self._set_status("凭证信息加载成功", "green")
        self._enable_buttons()
    
    def _update_token(self):
        new_token = self.new_token_text.get(1.0, tk.END).strip()
        
        if not new_token:
            messagebox.showwarning("警告", "请输入新的 Access Token")
            return
        
        try:
            hours = int(self.expire_hours.get())
            if hours < 1:
                messagebox.showwarning("警告", "过期时间必须至少为 1 小时")
                return
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的过期小时数")
            return
        
        confirm = messagebox.askyesno("确认更新", 
                                      f"确定要更新 Access Token 吗?\n\n"
                                      f"过期时间: {hours} 小时\n"
                                      f"Token 长度: {len(new_token)} 字符")
        
        if not confirm:
            return
        
        self._set_status("正在更新凭证...", "blue")
        self._disable_buttons()
        
        def update_task():
            try:
                expire_at = int(datetime.datetime.now().timestamp() * 1000) + (hours * 3600 * 1000)
                
                # 构建JSON（无空格，紧凑格式，与自然登录一致）
                token_data = {
                    "accessToken": new_token,
                    "expireAt": expire_at
                }
                password_json = json.dumps(token_data, separators=(',', ':'), ensure_ascii=False)
                
                # 使用ctypes直接写入UTF-8格式
                # 写入到当前使用的目标名称
                write_credential_utf8(
                    self.target_name,
                    "access-token",
                    password_json
                )
                
                # 更新成功后自动重启Verdent
                self.root.after(0, lambda: self._set_status("Token 更新成功，正在重启Verdent...", "green"))
                
                # 尝试重启Verdent
                try:
                    if self.verdent_manager.restart_verdent():
                        self.root.after(0, lambda: messagebox.showinfo(
                            "成功", 
                            "Access Token 已成功更新!\n\nVerdent 已自动重启以应用新的Token。"
                        ))
                    else:
                        # 如果找不到Verdent，询问用户是否手动指定
                        def ask_for_verdent():
                            result = messagebox.askyesno(
                                "Verdent未找到",
                                "Token已更新，但无法自动重启Verdent。\n\n是否要手动选择Verdent.exe文件？"
                            )
                            if result:
                                if self.verdent_manager.browse_for_verdent():
                                    messagebox.showinfo("成功", "Verdent 已启动")
                                else:
                                    messagebox.showinfo(
                                        "提示", 
                                        "Token已更新。\n\n请手动重启Verdent以应用新的Token。"
                                    )
                            else:
                                messagebox.showinfo(
                                    "提示", 
                                    "Token已更新。\n\n请手动重启Verdent以应用新的Token。"
                                )
                        self.root.after(0, ask_for_verdent)
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showwarning(
                        "部分成功",
                        f"Token已更新，但重启Verdent时出错：{str(e)}\n\n请手动重启Verdent。"
                    ))
                
                self.root.after(1000, self._load_current_token)
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"更新失败: {str(e)}", "red"))
                self.root.after(0, lambda: messagebox.showerror("错误", f"更新失败:\n{str(e)}"))
                self.root.after(0, self._enable_buttons)
        
        threading.Thread(target=update_task, daemon=True).start()
    
    def _copy_current_token(self):
        current_token = self.current_token_text.get(1.0, tk.END).strip()
        if current_token:
            self.root.clipboard_clear()
            self.root.clipboard_append(current_token)
            self._set_status("当前 Token 已复制到剪贴板", "green")
        else:
            self._set_status("没有可复制的 Token", "red")
    
    def _set_status(self, message, color):
        self.status_label.config(text=message, foreground=color)
    
    def _disable_buttons(self):
        self.update_button.config(state=tk.DISABLED)
        self.refresh_button.config(state=tk.DISABLED)
        self.copy_button.config(state=tk.DISABLED)
    
    def _enable_buttons(self):
        self.update_button.config(state=tk.NORMAL)
        self.refresh_button.config(state=tk.NORMAL)
        self.copy_button.config(state=tk.NORMAL)
    
    def _restart_verdent(self):
        """重启Verdent软件"""
        self._set_status("正在重启Verdent...", "blue")
        try:
            if self.verdent_manager.restart_verdent():
                self._set_status("Verdent已重启", "green")
                messagebox.showinfo("成功", "Verdent软件已重新启动")
            else:
                # 尝试让用户手动选择Verdent位置
                result = messagebox.askyesno(
                    "未找到Verdent",
                    "无法自动找到Verdent的安装位置。\n\n是否要手动选择Verdent.exe文件？"
                )
                if result:
                    if self.verdent_manager.browse_for_verdent():
                        self._set_status("Verdent已启动", "green")
                        messagebox.showinfo("成功", "Verdent软件已启动")
                    else:
                        self._set_status("启动取消", "orange")
                else:
                    self._set_status("需要手动启动", "orange")
                    messagebox.showinfo("提示", "请手动从开始菜单或桌面启动Verdent")
        except Exception as e:
            self._set_status(f"重启失败: {str(e)}", "red")
            messagebox.showerror("错误", f"重启失败：\n{str(e)}")
    
    def _change_machine_guid(self):
        """更换机器码"""
        result = messagebox.askyesno(
            "确认更换",
            "确定要更换系统机器码吗？\n\n" +
            "这将生成一个新的随机机器码。\n" +
            "原始机器码会被备份，可以随时还原。"
        )
        
        if not result:
            return
        
        try:
            new_guid = self.verdent_manager.change_machine_guid()
            # 直接在主界面更新显示
            self._display_machine_guid()
            self._set_status(f"机器码已更换: {new_guid[:20]}...", "green")
            # 不弹出消息框，只在状态栏显示
        except Exception as e:
            self._set_status(f"更换失败: {str(e)}", "red")
            messagebox.showerror("错误", f"更换机器码失败：\n{str(e)}")
    
    def _restore_machine_guid(self):
        """还原机器码"""
        result = messagebox.askyesno(
            "确认还原",
            "确定要还原到原始机器码吗？\n\n" +
            "这将恢复系统初始的机器码设置。"
        )
        
        if not result:
            return
        
        try:
            original_guid = self.verdent_manager.restore_machine_guid()
            # 直接在主界面更新显示
            self._display_machine_guid()
            self._set_status(f"机器码已还原: {original_guid[:20]}...", "green")
            # 不弹出消息框，只在状态栏显示
        except Exception as e:
            self._set_status(f"还原失败: {str(e)}", "red")
            messagebox.showerror("错误", f"还原机器码失败：\n{str(e)}")
    
    def _view_machine_guid(self):
        """查看当前机器码"""
        self._display_machine_guid()
    
    def _display_machine_guid(self):
        """在主界面显示机器码信息"""
        try:
            current_guid = self.verdent_manager.get_current_machine_guid()
            self.guid_label.config(text=current_guid, foreground="blue")
            
            # 显示备份信息
            if os.path.exists(self.verdent_manager.backup_file):
                with open(self.verdent_manager.backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                    original_guid = backup_data.get("original_machine_guid", "未知")
                    
                    self.original_guid_label.config(text=original_guid, foreground="gray")
                    
                    if current_guid == original_guid:
                        self.init_status_label.config(
                            text="使用原始机器码", 
                            foreground="green"
                        )
                    else:
                        # 查找修改历史
                        modified_guids = backup_data.get("modified_guids", [])
                        if modified_guids:
                            last_mod = modified_guids[-1]
                            mod_time = last_mod.get('modified_time', '未知')
                            # 格式化时间
                            try:
                                dt = datetime.datetime.fromisoformat(mod_time)
                                mod_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                pass
                            self.init_status_label.config(
                                text=f"已修改 ({mod_time})", 
                                foreground="orange"
                            )
                        else:
                            self.init_status_label.config(
                                text="使用修改后的机器码", 
                                foreground="orange"
                            )
            else:
                self.original_guid_label.config(text="无备份记录", foreground="gray")
                self.init_status_label.config(text="未备份", foreground="orange")
                
        except Exception as e:
            self.guid_label.config(text=f"读取失败: {str(e)}", foreground="red")
            self._set_status(f"读取机器码失败: {str(e)}", "red")


def main():
    root = tk.Tk()
    app = TokenChangerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        messagebox.showerror("错误", f"程序启动失败:\n{str(e)}")
        sys.exit(1)
