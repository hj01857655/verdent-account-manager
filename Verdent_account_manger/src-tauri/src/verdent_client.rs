use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Command;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum VerdentClientError {
    #[error("Verdent 客户端未安装或未找到")]
    NotInstalled,
    
    #[error("写入凭证失败: {0}")]
    CredentialWriteError(String),
    
    #[error("重置机器码失败: {0}")]
    MachineGuidResetError(String),
    
    #[error("重启进程失败: {0}")]
    RestartError(String),
    
    #[error("不支持的操作系统")]
    UnsupportedOS,
    
    #[error("需要管理员权限")]
    PermissionDenied,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct VerdentClientManager {
    #[serde(skip)]
    verdent_exe_path: Option<PathBuf>,
}

impl VerdentClientManager {
    pub fn new() -> Self {
        Self {
            verdent_exe_path: None,
        }
    }

    /// 查找 Verdent 客户端安装路径（支持自定义路径）
    pub fn find_verdent_path(&mut self, custom_path: Option<&str>) -> Result<PathBuf, VerdentClientError> {
        #[cfg(target_os = "windows")]
        {
            // 首先检查用户自定义路径
            if let Some(custom) = custom_path {
                println!("[*] 检查用户自定义路径: {}", custom);
                let path = PathBuf::from(custom);
                if path.exists() && path.is_file() {
                    println!("[✓] 使用用户自定义 Verdent 客户端: {}", path.display());
                    self.verdent_exe_path = Some(path.clone());
                    return Ok(path);
                } else {
                    println!("[!] 自定义路径无效 (不存在或不是文件): {}", custom);
                }
            } else {
                println!("[*] 未设置自定义路径，尝试默认路径...");
            }

            // 然后检查默认路径
            let possible_paths = vec![
                std::env::var("LOCALAPPDATA")
                    .ok()
                    .map(|p| PathBuf::from(p).join("Programs").join("verdent").join("Verdent.exe")),
                std::env::var("LOCALAPPDATA")
                    .ok()
                    .map(|p| PathBuf::from(p).join("Programs").join("verdent-deck").join("Verdent.exe")),
                Some(PathBuf::from(r"C:\Program Files\Verdent\Verdent.exe")),
                Some(PathBuf::from(r"C:\Program Files (x86)\Verdent\Verdent.exe")),
            ];

            for path in possible_paths.into_iter().flatten() {
                if path.exists() {
                    println!("[✓] 找到 Verdent 客户端: {}", path.display());
                    self.verdent_exe_path = Some(path.clone());
                    return Ok(path);
                }
            }
        }

        #[cfg(target_os = "macos")]
        {
            let possible_paths = vec![
                Some(PathBuf::from("/Applications/Verdent.app")),
                dirs::home_dir().map(|p| p.join("Applications").join("Verdent.app")),
            ];

            for path in possible_paths.into_iter().flatten() {
                if path.exists() {
                    println!("[✓] 找到 Verdent 客户端: {}", path.display());
                    self.verdent_exe_path = Some(path.clone());
                    return Ok(path);
                }
            }
        }

        #[cfg(target_os = "linux")]
        {
            // Linux 通常安装在 /opt 或用户目录
            let possible_paths = vec![
                Some(PathBuf::from("/opt/Verdent/verdent")),
                dirs::home_dir().map(|p| p.join(".local").join("bin").join("verdent")),
            ];

            for path in possible_paths.into_iter().flatten() {
                if path.exists() {
                    println!("[✓] 找到 Verdent 客户端: {}", path.display());
                    self.verdent_exe_path = Some(path.clone());
                    return Ok(path);
                }
            }
        }

        Err(VerdentClientError::NotInstalled)
    }

    /// 写入 Token 到 Verdent 客户端配置
    /// Windows: 使用 Windows Credential Manager
    /// macOS: 使用 Keychain
    /// Linux: 使用配置文件
    pub fn write_token(&self, token: &str, expire_at: i64) -> Result<(), VerdentClientError> {
        #[cfg(target_os = "windows")]
        {
            self.write_token_windows(token, expire_at)
        }

        #[cfg(target_os = "macos")]
        {
            self.write_token_macos(token, expire_at)
        }

        #[cfg(target_os = "linux")]
        {
            self.write_token_linux(token, expire_at)
        }

        #[cfg(not(any(target_os = "windows", target_os = "macos", target_os = "linux")))]
        {
            Err(VerdentClientError::UnsupportedOS)
        }
    }

    /// Windows: 使用 Windows Credential Manager 写入凭证
    #[cfg(target_os = "windows")]
    fn write_token_windows(&self, token: &str, expire_at: i64) -> Result<(), VerdentClientError> {
        use windows::core::PWSTR;
        use windows::Win32::Foundation::FILETIME;
        use windows::Win32::Security::Credentials::{
            CredWriteW, CREDENTIALW, CRED_FLAGS, CRED_PERSIST_ENTERPRISE, CRED_TYPE_GENERIC,
        };

        // 构建 JSON 格式的凭证数据
        let credential_data = serde_json::json!({
            "accessToken": token,
            "expireAt": expire_at
        });
        let password_json = serde_json::to_string(&credential_data)
            .map_err(|e| VerdentClientError::CredentialWriteError(e.to_string()))?;

        println!("[*] 凭证 JSON 数据: {}", password_json);
        println!("[*] JSON 长度: {} 字节", password_json.len());

        // 将 JSON 转换为 UTF-8 字节
        let password_bytes = password_json.as_bytes();

        // 凭证目标名称 (兼容新旧两种命名)
        let target_names = vec![
            "LegacyGeneric:target=ai.verdent.deck/access-token",
        ];

        // 用户名
        let username = "access-token";

        // 写入两个凭证（兼容性）
        for target_name in &target_names {
            println!("[*] 写入凭证到: {}", target_name);

            // 将字符串转换为 UTF-16 (Windows API 需要)
            let target_name_wide: Vec<u16> = target_name.encode_utf16().chain(std::iter::once(0)).collect();
            let username_wide: Vec<u16> = username.encode_utf16().chain(std::iter::once(0)).collect();

            // 创建 CREDENTIAL 结构
            let mut cred = CREDENTIALW {
                Flags: CRED_FLAGS(0),
                Type: CRED_TYPE_GENERIC,
                TargetName: PWSTR::from_raw(target_name_wide.as_ptr() as *mut u16),
                Comment: PWSTR::null(),
                LastWritten: FILETIME { dwLowDateTime: 0, dwHighDateTime: 0 },
                CredentialBlobSize: password_bytes.len() as u32,
                CredentialBlob: password_bytes.as_ptr() as *mut u8,
                Persist: CRED_PERSIST_ENTERPRISE,
                AttributeCount: 0,
                Attributes: std::ptr::null_mut(),
                TargetAlias: PWSTR::null(),
                UserName: PWSTR::from_raw(username_wide.as_ptr() as *mut u16),
            };

            // 调用 Windows API 写入凭证
            unsafe {
                CredWriteW(&mut cred, 0)
                    .map_err(|e| VerdentClientError::CredentialWriteError(format!(
                        "写入凭证失败 ({}): {}",
                        target_name,
                        e
                    )))?;
            }

            println!("[✓] 凭证已写入: {}", target_name);
        }

        println!("[✓] Token 已写入 Windows Credential Manager");
        Ok(())
    }

    /// macOS: 使用 Keychain 写入凭证
    #[cfg(target_os = "macos")]
    fn write_token_macos(&self, token: &str, expire_at: i64) -> Result<(), VerdentClientError> {
        // 构建 JSON 格式的凭证数据
        let credential_data = serde_json::json!({
            "accessToken": token,
            "expireAt": expire_at
        });
        let password_json = serde_json::to_string(&credential_data)
            .map_err(|e| VerdentClientError::CredentialWriteError(e.to_string()))?;

        let service_name = "ai.verdent.deck";
        let account_name = "access-token";

        // 先删除旧凭证
        let _ = Command::new("security")
            .args(&["delete-generic-password", "-s", service_name, "-a", account_name])
            .output();

        // 添加新凭证
        let output = Command::new("security")
            .args(&[
                "add-generic-password",
                "-s", service_name,
                "-a", account_name,
                "-w", &password_json,
                "-U", // 更新已存在的凭证
            ])
            .output()
            .map_err(|e| VerdentClientError::CredentialWriteError(format!("执行 security 命令失败: {}", e)))?;

        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            return Err(VerdentClientError::CredentialWriteError(format!(
                "写入 Keychain 失败: {}",
                error_msg
            )));
        }

        println!("[✓] Token 已写入 macOS Keychain");
        Ok(())
    }

    /// Linux: 使用配置文件写入凭证
    #[cfg(target_os = "linux")]
    fn write_token_linux(&self, token: &str, expire_at: i64) -> Result<(), VerdentClientError> {
        // Linux 通常使用配置文件存储
        let config_dir = dirs::config_dir()
            .ok_or_else(|| VerdentClientError::CredentialWriteError("无法获取配置目录".to_string()))?
            .join("verdent");

        std::fs::create_dir_all(&config_dir)
            .map_err(|e| VerdentClientError::CredentialWriteError(format!("创建配置目录失败: {}", e)))?;

        let config_file = config_dir.join("credentials.json");

        let credential_data = serde_json::json!({
            "accessToken": token,
            "expireAt": expire_at
        });

        std::fs::write(&config_file, serde_json::to_string_pretty(&credential_data).unwrap())
            .map_err(|e| VerdentClientError::CredentialWriteError(format!("写入配置文件失败: {}", e)))?;

        println!("[✓] Token 已写入配置文件: {}", config_file.display());
        Ok(())
    }

    /// 重置机器码
    pub fn reset_machine_guid(&self) -> Result<String, VerdentClientError> {
        #[cfg(target_os = "windows")]
        {
            self.reset_machine_guid_windows()
        }

        #[cfg(not(target_os = "windows"))]
        {
            // macOS 和 Linux 不需要重置机器码
            println!("[*] 当前操作系统不需要重置机器码");
            Ok("N/A".to_string())
        }
    }

    /// Windows: 重置注册表中的 MachineGuid
    #[cfg(target_os = "windows")]
    fn reset_machine_guid_windows(&self) -> Result<String, VerdentClientError> {
        use uuid::Uuid;

        // 生成新的 GUID (大写，无花括号，格式如: 3840DC62-7506-4F6C-A70F-79D5FC150433)
        let new_guid = Uuid::new_v4().to_string().to_uppercase();

        // 使用 reg 命令修改注册表 (需要管理员权限)
        let output = Command::new("reg")
            .args(&[
                "add",
                r"HKLM\SOFTWARE\Microsoft\Cryptography",
                "/v", "MachineGuid",
                "/t", "REG_SZ",
                "/d", &new_guid,
                "/f",
            ])
            .output()
            .map_err(|e| VerdentClientError::MachineGuidResetError(format!("执行 reg 命令失败: {}", e)))?;

        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);

            // 检查是否是权限问题
            if error_msg.contains("拒绝访问") || error_msg.contains("Access is denied") {
                return Err(VerdentClientError::PermissionDenied);
            }

            return Err(VerdentClientError::MachineGuidResetError(format!(
                "修改注册表失败: {}",
                error_msg
            )));
        }

        println!("[✓] 机器码已重置为: {}", new_guid);
        Ok(new_guid)
    }

    /// 终止 Verdent 进程
    pub fn kill_verdent_process(&self) -> Result<u32, VerdentClientError> {
        #[cfg(target_os = "windows")]
        {
            let output = Command::new("taskkill")
                .args(&["/F", "/IM", "Verdent.exe"])
                .output()
                .map_err(|e| VerdentClientError::RestartError(format!("执行 taskkill 失败: {}", e)))?;

            if output.status.success() {
                println!("[✓] Verdent 进程已终止");
                Ok(1)
            } else {
                // 进程可能不存在,不算错误
                println!("[*] Verdent 进程未运行");
                Ok(0)
            }
        }

        #[cfg(target_os = "macos")]
        {
            let output = Command::new("pkill")
                .args(&["-9", "Verdent"])
                .output()
                .map_err(|e| VerdentClientError::RestartError(format!("执行 pkill 失败: {}", e)))?;

            if output.status.success() {
                println!("[✓] Verdent 进程已终止");
                Ok(1)
            } else {
                println!("[*] Verdent 进程未运行");
                Ok(0)
            }
        }

        #[cfg(target_os = "linux")]
        {
            let output = Command::new("pkill")
                .args(&["-9", "verdent"])
                .output()
                .map_err(|e| VerdentClientError::RestartError(format!("执行 pkill 失败: {}", e)))?;

            if output.status.success() {
                println!("[✓] Verdent 进程已终止");
                Ok(1)
            } else {
                println!("[*] Verdent 进程未运行");
                Ok(0)
            }
        }
    }

    /// 启动 Verdent 客户端
    pub fn start_verdent(&mut self) -> Result<(), VerdentClientError> {
        let exe_path = if let Some(path) = &self.verdent_exe_path {
            path.clone()
        } else {
            self.find_verdent_path(None)?
        };

        #[cfg(target_os = "windows")]
        {
            Command::new(&exe_path)
                .spawn()
                .map_err(|e| VerdentClientError::RestartError(format!("启动 Verdent 失败: {}", e)))?;
        }

        #[cfg(target_os = "macos")]
        {
            Command::new("open")
                .arg(&exe_path)
                .spawn()
                .map_err(|e| VerdentClientError::RestartError(format!("启动 Verdent 失败: {}", e)))?;
        }

        #[cfg(target_os = "linux")]
        {
            Command::new(&exe_path)
                .spawn()
                .map_err(|e| VerdentClientError::RestartError(format!("启动 Verdent 失败: {}", e)))?;
        }

        println!("[✓] Verdent 客户端已启动");
        Ok(())
    }

    /// 重启 Verdent 客户端
    pub fn restart_verdent(&mut self) -> Result<(), VerdentClientError> {
        println!("[*] 正在重启 Verdent 客户端...");

        // 1. 终止进程
        self.kill_verdent_process()?;

        // 2. 等待进程完全终止 (与 Python 脚本保持一致，等待3秒)
        println!("[*] 等待进程完全终止...");
        std::thread::sleep(std::time::Duration::from_secs(3));

        // 3. 清理临时 socket 文件 (解决权限问题)
        #[cfg(target_os = "windows")]
        {
            if let Ok(temp_dir) = std::env::var("TEMP") {
                let socket_dir = PathBuf::from(temp_dir).join("verdent-sockets");
                if socket_dir.exists() {
                    println!("[*] 清理临时 socket 文件夹: {}", socket_dir.display());
                    let _ = std::fs::remove_dir_all(&socket_dir);
                }
            }
        }

        // 4. 启动进程
        self.start_verdent()?;

        println!("[✓] Verdent 客户端重启完成");
        Ok(())
    }
}


