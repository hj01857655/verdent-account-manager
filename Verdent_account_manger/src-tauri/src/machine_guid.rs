use serde::{Deserialize, Serialize};
use std::process::Command;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MachineGuidInfo {
    pub current_guid: Option<String>,
    pub backup_guid: Option<String>,
    pub has_backup: bool,
    pub platform: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MachineGuidBackup {
    pub original_guid: String,
    pub backup_time: String,
}

/// 机器码管理器
pub struct MachineGuidManager {
    backup_file: std::path::PathBuf,
}

impl MachineGuidManager {
    pub fn new() -> Result<Self, String> {
        let storage_dir = dirs::home_dir()
            .ok_or_else(|| "无法获取主目录".to_string())?
            .join(".verdent_accounts");
        
        std::fs::create_dir_all(&storage_dir)
            .map_err(|e| format!("创建存储目录失败: {}", e))?;
        
        let backup_file = storage_dir.join("machine_guid_backup.json");
        
        Ok(Self { backup_file })
    }

    /// 读取当前机器码
    pub fn read_current_guid(&self) -> Result<Option<String>, String> {
        #[cfg(target_os = "windows")]
        {
            self.read_windows_guid()
        }

        #[cfg(not(target_os = "windows"))]
        {
            Ok(None)
        }
    }

    /// Windows: 从注册表读取机器码
    #[cfg(target_os = "windows")]
    fn read_windows_guid(&self) -> Result<Option<String>, String> {
        let output = Command::new("reg")
            .args(&["query", "HKLM\\SOFTWARE\\Microsoft\\Cryptography", "/v", "MachineGuid"])
            .output()
            .map_err(|e| format!("执行 reg 命令失败: {}", e))?;

        if !output.status.success() {
            return Err("读取注册表失败".to_string());
        }

        let output_str = String::from_utf8_lossy(&output.stdout);
        
        // 解析输出: MachineGuid    REG_SZ    {GUID}
        for line in output_str.lines() {
            if line.contains("MachineGuid") && line.contains("REG_SZ") {
                let parts: Vec<&str> = line.split_whitespace().collect();
                if parts.len() >= 3 {
                    return Ok(Some(parts[2].to_string()));
                }
            }
        }

        Ok(None)
    }

    /// 读取备份的机器码
    pub fn read_backup_guid(&self) -> Result<Option<MachineGuidBackup>, String> {
        if !self.backup_file.exists() {
            return Ok(None);
        }

        let content = std::fs::read_to_string(&self.backup_file)
            .map_err(|e| format!("读取备份文件失败: {}", e))?;
        
        let backup: MachineGuidBackup = serde_json::from_str(&content)
            .map_err(|e| format!("解析备份文件失败: {}", e))?;
        
        Ok(Some(backup))
    }

    /// 备份当前机器码
    pub fn backup_current_guid(&self) -> Result<String, String> {
        // 检查是否已有备份
        if self.backup_file.exists() {
            return Err("已存在备份,无需重复备份".to_string());
        }

        // 读取当前机器码
        let current_guid = self.read_current_guid()?
            .ok_or_else(|| "无法读取当前机器码".to_string())?;

        // 创建备份
        let backup = MachineGuidBackup {
            original_guid: current_guid.clone(),
            backup_time: chrono::Utc::now().to_rfc3339(),
        };

        // 保存备份
        let json = serde_json::to_string_pretty(&backup)
            .map_err(|e| format!("序列化备份数据失败: {}", e))?;
        
        std::fs::write(&self.backup_file, json)
            .map_err(|e| format!("写入备份文件失败: {}", e))?;

        Ok(current_guid)
    }

    /// 重置机器码为新的随机 GUID
    pub fn reset_to_new_guid(&self) -> Result<String, String> {
        // 如果没有备份,先备份
        if !self.backup_file.exists() {
            self.backup_current_guid()?;
        }

        // 生成新的 GUID (不带花括号，格式如: 3840DC62-7506-4F6C-A70F-79D5FC150433)
        let new_guid = Uuid::new_v4().to_string().to_uppercase();

        // 写入注册表
        self.write_windows_guid(&new_guid)?;

        Ok(new_guid)
    }

    /// 恢复到备份的机器码
    pub fn restore_backup_guid(&self) -> Result<String, String> {
        let backup = self.read_backup_guid()?
            .ok_or_else(|| "没有找到备份的机器码".to_string())?;

        // 写入注册表
        self.write_windows_guid(&backup.original_guid)?;

        Ok(backup.original_guid)
    }

    /// Windows: 写入机器码到注册表
    #[cfg(target_os = "windows")]
    fn write_windows_guid(&self, guid: &str) -> Result<(), String> {
        println!("[*] 准备写入机器码到注册表: {}", guid);

        // 使用 reg add 命令写入注册表
        // 需要管理员权限
        let output = Command::new("reg")
            .args(&[
                "add",
                "HKLM\\SOFTWARE\\Microsoft\\Cryptography",
                "/v",
                "MachineGuid",
                "/t",
                "REG_SZ",
                "/d",
                guid,
                "/f"
            ])
            .output()
            .map_err(|e| {
                eprintln!("[×] 执行 reg 命令失败: {}", e);
                format!("执行 reg 命令失败: {}\n\n需要管理员权限才能修改系统注册表", e)
            })?;

        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            eprintln!("[×] 写入注册表失败: {}", error_msg);

            // 检查是否是权限问题
            if error_msg.contains("拒绝访问") || error_msg.contains("Access is denied") {
                return Err("❌ 权限不足\n\n修改系统注册表需要管理员权限。\n请以管理员身份运行此程序。".to_string());
            }

            return Err(format!("写入注册表失败: {}\n\n请以管理员身份运行此程序", error_msg));
        }

        println!("[✓] 机器码已成功写入注册表");
        Ok(())
    }

    /// 非 Windows 平台的占位实现
    #[cfg(not(target_os = "windows"))]
    fn write_windows_guid(&self, _guid: &str) -> Result<(), String> {
        Err("此功能仅支持 Windows 平台".to_string())
    }

    /// 获取机器码信息
    pub fn get_info(&self) -> Result<MachineGuidInfo, String> {
        let current_guid = self.read_current_guid()?;
        let backup = self.read_backup_guid()?;

        let platform = if cfg!(target_os = "windows") {
            "Windows".to_string()
        } else if cfg!(target_os = "macos") {
            "macOS".to_string()
        } else {
            "Linux".to_string()
        };

        Ok(MachineGuidInfo {
            current_guid,
            backup_guid: backup.as_ref().map(|b| b.original_guid.clone()),
            has_backup: backup.is_some(),
            platform,
        })
    }

    /// 删除备份
    pub fn delete_backup(&self) -> Result<(), String> {
        if self.backup_file.exists() {
            std::fs::remove_file(&self.backup_file)
                .map_err(|e| format!("删除备份文件失败: {}", e))?;
        }
        Ok(())
    }
}

