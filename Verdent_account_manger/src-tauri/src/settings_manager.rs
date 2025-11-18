use serde::{Deserialize, Serialize};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::sync::Mutex;
use chrono::Utc;
use thiserror::Error;
use once_cell::sync::Lazy;

// 全局文件锁，防止并发写入
static SETTINGS_LOCK: Lazy<Mutex<()>> = Lazy::new(|| Mutex::new(()));

#[derive(Debug, Error)]
pub enum SettingsError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserSettings {
    pub current_account_id: Option<String>,      // 当前使用的账号ID
    pub email_privacy_mode: bool,                // 邮箱隐私模式
    pub selected_accounts: Vec<String>,          // 已选择的账号ID列表
    pub filter_type: Option<String>,             // 当前筛选类型
    pub import_mode: String,                     // 导入模式 (token/account/json)
    pub export_format: String,                   // 导出格式 (json/txt/csv)
    pub register_count: i32,                     // 自动注册数量 (1-10)
    pub register_max_workers: i32,               // 并发数 (1-5)
    pub register_password: String,               // 默认密码
    pub register_use_random_password: bool,      // 是否使用随机密码
    pub register_headless: bool,                 // 无头模式 (后台运行)
    pub verdent_exe_path: Option<String>,        // Verdent.exe 自定义路径
    pub last_updated: String,                    // 最后更新时间
}

impl Default for UserSettings {
    fn default() -> Self {
        Self {
            current_account_id: None,
            email_privacy_mode: false,
            selected_accounts: Vec::new(),
            filter_type: None,
            import_mode: "token".to_string(),
            export_format: "json".to_string(),
            register_count: 1,
            register_max_workers: 2,
            register_password: "VerdentAI@2024".to_string(),
            register_use_random_password: false,
            register_headless: false,
            verdent_exe_path: None,
            last_updated: Utc::now().to_rfc3339(),
        }
    }
}

pub struct SettingsManager {
    storage_path: PathBuf,
}

impl SettingsManager {
    pub fn new() -> Result<Self, SettingsError> {
        // 使用与账户相同的目录
        let storage_dir = dirs::home_dir()
            .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "Home directory not found"))?
            .join(".verdent_accounts");

        fs::create_dir_all(&storage_dir)?;

        let storage_path = storage_dir.join("user_settings.json");

        // 如果设置文件不存在，创建默认设置（使用文件锁）
        if !storage_path.exists() {
            let _lock = SETTINGS_LOCK.lock().unwrap();

            // 双重检查：获取锁后再次检查文件是否存在
            if !storage_path.exists() {
                println!("[SettingsManager::new] 配置文件不存在，创建默认配置");
                let initial_settings = UserSettings::default();
                let content = serde_json::to_string_pretty(&initial_settings)?;

                // 使用原子写入
                let temp_path = storage_path.with_extension("tmp");
                let mut file = OpenOptions::new()
                    .write(true)
                    .create(true)
                    .truncate(true)
                    .open(&temp_path)?;

                file.write_all(content.as_bytes())?;
                file.sync_all()?;
                drop(file);

                fs::rename(&temp_path, &storage_path)?;
                println!("[SettingsManager::new] ✓ 默认配置已创建");
            }
        }

        Ok(Self { storage_path })
    }
    
    pub fn load(&self) -> Result<UserSettings, SettingsError> {
        // 获取文件锁
        let _lock = SETTINGS_LOCK.lock().unwrap();

        let content = fs::read_to_string(&self.storage_path)?;
        Ok(serde_json::from_str(&content)?)
    }

    pub fn save(&self, settings: &UserSettings) -> Result<(), SettingsError> {
        // 获取文件锁，防止并发写入
        let _lock = SETTINGS_LOCK.lock().unwrap();

        println!("[SettingsManager::save] 准备保存配置:");
        println!("  - verdent_exe_path: {:?}", settings.verdent_exe_path);
        println!("  - current_account_id: {:?}", settings.current_account_id);

        let mut settings_with_timestamp = settings.clone();
        settings_with_timestamp.last_updated = Utc::now().to_rfc3339();

        let content = serde_json::to_string_pretty(&settings_with_timestamp)?;

        // 使用原子写入：先写入临时文件，再重命名
        let temp_path = self.storage_path.with_extension("tmp");

        // 写入临时文件并强制刷新到磁盘
        let mut file = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(&temp_path)?;

        file.write_all(content.as_bytes())?;
        file.sync_all()?;  // 强制刷新到磁盘
        drop(file);  // 关闭文件

        // 原子重命名
        fs::rename(&temp_path, &self.storage_path)?;

        println!("[SettingsManager::save] ✓ 配置文件已原子写入并刷新到磁盘");

        // 验证保存是否成功
        let verified = self.load_without_lock()?;
        println!("[SettingsManager::save] 验证保存结果:");
        println!("  - verdent_exe_path: {:?}", verified.verdent_exe_path);
        println!("  - current_account_id: {:?}", verified.current_account_id);

        if verified.verdent_exe_path != settings.verdent_exe_path {
            eprintln!("[SettingsManager::save] ✗ 警告：verdent_exe_path 保存后不一致！");
            eprintln!("  期望: {:?}", settings.verdent_exe_path);
            eprintln!("  实际: {:?}", verified.verdent_exe_path);
        }

        Ok(())
    }

    // 内部方法：不加锁的 load（仅用于 save 方法内部验证）
    fn load_without_lock(&self) -> Result<UserSettings, SettingsError> {
        let content = fs::read_to_string(&self.storage_path)?;
        Ok(serde_json::from_str(&content)?)
    }
    
    pub fn update_current_account(&self, account_id: Option<String>) -> Result<(), SettingsError> {
        println!("[SettingsManager::update_current_account] 开始更新当前账号ID: {:?}", account_id);

        let mut settings = self.load()?;
        println!("[SettingsManager::update_current_account] 加载的配置:");
        println!("  - current_account_id: {:?}", settings.current_account_id);
        println!("  - verdent_exe_path: {:?}", settings.verdent_exe_path);
        println!("  - email_privacy_mode: {}", settings.email_privacy_mode);

        settings.current_account_id = account_id.clone();
        println!("[SettingsManager::update_current_account] 更新后的配置:");
        println!("  - current_account_id: {:?}", settings.current_account_id);
        println!("  - verdent_exe_path: {:?}", settings.verdent_exe_path);

        self.save(&settings)?;
        println!("[SettingsManager::update_current_account] ✓ 配置已保存");

        Ok(())
    }
    
    pub fn update_email_privacy(&self, privacy_mode: bool) -> Result<(), SettingsError> {
        let mut settings = self.load()?;
        settings.email_privacy_mode = privacy_mode;
        self.save(&settings)?;
        Ok(())
    }
    
    pub fn update_selected_accounts(&self, selected: Vec<String>) -> Result<(), SettingsError> {
        let mut settings = self.load()?;
        settings.selected_accounts = selected;
        self.save(&settings)?;
        Ok(())
    }
    
    pub fn update_filter_type(&self, filter_type: Option<String>) -> Result<(), SettingsError> {
        let mut settings = self.load()?;
        settings.filter_type = filter_type;
        self.save(&settings)?;
        Ok(())
    }
    
    pub fn update_register_config(
        &self, 
        count: i32, 
        max_workers: i32, 
        password: String, 
        use_random_password: bool, 
        headless: bool
    ) -> Result<(), SettingsError> {
        let mut settings = self.load()?;
        settings.register_count = count;
        settings.register_max_workers = max_workers;
        settings.register_password = password;
        settings.register_use_random_password = use_random_password;
        settings.register_headless = headless;
        self.save(&settings)?;
        Ok(())
    }
    
    pub fn update_verdent_exe_path(&self, path: Option<String>) -> Result<(), SettingsError> {
        println!("[SettingsManager] 更新 Verdent.exe 路径: {:?}", path);
        println!("[SettingsManager] 配置文件路径: {:?}", self.storage_path);

        let mut settings = self.load()?;
        println!("[SettingsManager] 当前设置: verdent_exe_path = {:?}", settings.verdent_exe_path);

        settings.verdent_exe_path = path.clone();
        println!("[SettingsManager] 新设置: verdent_exe_path = {:?}", settings.verdent_exe_path);

        self.save(&settings)?;
        println!("[SettingsManager] ✓ 设置已保存到文件");

        // 验证保存是否成功
        let verified = self.load()?;
        println!("[SettingsManager] 验证读取: verdent_exe_path = {:?}", verified.verdent_exe_path);

        if verified.verdent_exe_path == path {
            println!("[SettingsManager] ✓ 验证成功：路径已正确保存");
        } else {
            println!("[SettingsManager] ✗ 验证失败：保存的路径与预期不符");
        }

        Ok(())
    }
}
