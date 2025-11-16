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


class TokenChangerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Verdent Deck Access Token 更改器")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.target_name = "LegacyGeneric:target=ai.verdent.deck/access-token"
        
        self._create_widgets()
        self._load_current_token()
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(main_frame, text="Verdent Deck Access Token 管理器", 
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
        
        self.status_label = ttk.Label(main_frame, text="准备就绪", foreground="green")
        self.status_label.grid(row=6, column=0)
    
    def _load_current_token(self):
        self._set_status("正在加载凭证信息...", "blue")
        self._disable_buttons()
        
        def load_task():
            try:
                cred = read_credential_utf8(self.target_name)
                
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
                write_credential_utf8(
                    self.target_name,
                    "access-token",
                    password_json
                )
                
                self.root.after(0, lambda: self._set_status("Token 更新成功!", "green"))
                self.root.after(0, lambda: messagebox.showinfo("成功", "Access Token 已成功更新!\n\n请重启 Verdent Deck 应用以生效。"))
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
