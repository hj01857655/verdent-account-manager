use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use chrono::Utc;
use thiserror::Error;

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
        
        // 如果设置文件不存在，创建默认设置
        if !storage_path.exists() {
            let initial_settings = UserSettings::default();
            fs::write(&storage_path, serde_json::to_string_pretty(&initial_settings)?)?;
        }
        
        Ok(Self { storage_path })
    }
    
    pub fn load(&self) -> Result<UserSettings, SettingsError> {
        let content = fs::read_to_string(&self.storage_path)?;
        Ok(serde_json::from_str(&content)?)
    }
    
    pub fn save(&self, settings: &UserSettings) -> Result<(), SettingsError> {
        let mut settings_with_timestamp = settings.clone();
        settings_with_timestamp.last_updated = Utc::now().to_rfc3339();
        
        let content = serde_json::to_string_pretty(&settings_with_timestamp)?;
        fs::write(&self.storage_path, content)?;
        Ok(())
    }
    
    pub fn update_current_account(&self, account_id: Option<String>) -> Result<(), SettingsError> {
        let mut settings = self.load()?;
        settings.current_account_id = account_id;
        self.save(&settings)?;
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
}
