use std::fs;
use std::path::PathBuf;
use chrono::prelude::*;
use uuid;
use std::fs::OpenOptions;
use std::io::Write;
use std::sync::Mutex;

use crate::errors::AccountError;
use crate::models::{Account, AccountList};

pub struct AccountManager {
    storage_path: PathBuf,
    file_lock: Mutex<()>,  // 文件锁，防止并发写入
}

impl AccountManager {
    pub fn new() -> Result<Self, AccountError> {
        let storage_dir = dirs::home_dir()
            .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "Home directory not found"))?
            .join(".verdent_accounts");
        
        fs::create_dir_all(&storage_dir)?;
        
        let storage_path = storage_dir.join("accounts.json");
        
        if !storage_path.exists() {
            let initial_data = AccountList {
                accounts: Vec::new(),
                last_sync: Utc::now().to_rfc3339(),
            };
            fs::write(&storage_path, serde_json::to_string_pretty(&initial_data)?)?;
        }
        
        Ok(Self { 
            storage_path,
            file_lock: Mutex::new(()),
        })
    }
    
    pub fn get_storage_path(&self) -> String {
        self.storage_path.to_string_lossy().to_string()
    }
    
    fn load(&self) -> Result<AccountList, AccountError> {
        // 尝试读取主文件
        match fs::read_to_string(&self.storage_path) {
            Ok(content) => {
                match serde_json::from_str::<AccountList>(&content) {
                    Ok(data) => Ok(data),
                    Err(e) => {
                        eprintln!("[!] 主文件 JSON 格式错误: {}", e);
                        
                        // 尝试从备份文件恢复
                        let backup_path = self.storage_path.with_extension("backup");
                        if backup_path.exists() {
                            eprintln!("[*] 尝试从备份文件恢复...");
                            let backup_content = fs::read_to_string(&backup_path)?;
                            match serde_json::from_str::<AccountList>(&backup_content) {
                                Ok(data) => {
                                    eprintln!("[✓] 成功从备份恢复");
                                    // 恢复备份到主文件
                                    self.save(&data)?;
                                    Ok(data)
                                }
                                Err(_) => {
                                    eprintln!("[×] 备份文件也已损坏，创建新文件");
                                    Ok(AccountList::default())
                                }
                            }
                        } else {
                            eprintln!("[×] 无备份文件，创建新文件");
                            Ok(AccountList::default())
                        }
                    }
                }
            }
            Err(e) => Err(AccountError::from(e))
        }
    }
    
    fn save(&self, data: &AccountList) -> Result<(), AccountError> {
        // 获取文件锁，防止并发写入
        let _lock = self.file_lock.lock().unwrap();
        
        let content = serde_json::to_string_pretty(data)?;
        
        // 使用原子写入：先写入临时文件，再重命名
        let temp_path = self.storage_path.with_extension("tmp");
        
        // 创建备份文件（如果原文件存在）
        if self.storage_path.exists() {
            let backup_path = self.storage_path.with_extension("backup");
            let _ = fs::copy(&self.storage_path, &backup_path);
        }
        
        // 写入临时文件
        let mut file = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(&temp_path)?;
        
        file.write_all(content.as_bytes())?;
        file.sync_all()?;  // 确保数据写入磁盘
        drop(file);  // 关闭文件
        
        // 原子重命名
        fs::rename(&temp_path, &self.storage_path)?;
        
        Ok(())
    }
    
    pub fn add_account(&self, mut account: Account) -> Result<Account, AccountError> {
        let mut data = self.load()?;
        
        if account.id.is_empty() {
            account.id = uuid::Uuid::new_v4().to_string();
        }
        
        account.last_updated = Some(Utc::now().to_rfc3339());
        
        data.accounts.push(account.clone());
        data.last_sync = Utc::now().to_rfc3339();
        
        self.save(&data)?;
        Ok(account)
    }
    
    pub fn get_all_accounts(&self) -> Result<Vec<Account>, AccountError> {
        let data = self.load()?;
        Ok(data.accounts)
    }
    
    pub fn get_account(&self, id: &str) -> Result<Account, AccountError> {
        let data = self.load()?;
        data.accounts
            .into_iter()
            .find(|acc| acc.id == id)
            .ok_or_else(|| AccountError::NotFound(id.to_string()))
    }
    
    pub fn update_account(&self, id: &str, updated: Account) -> Result<Account, AccountError> {
        let mut data = self.load()?;
        
        let account = data.accounts
            .iter_mut()
            .find(|acc| acc.id == id)
            .ok_or_else(|| AccountError::NotFound(id.to_string()))?;
        
        *account = updated;
        account.last_updated = Some(Utc::now().to_rfc3339());
        let result = account.clone();
        data.last_sync = Utc::now().to_rfc3339();
        
        self.save(&data)?;
        Ok(result)
    }
    
    pub fn delete_account(&self, id: &str) -> Result<(), AccountError> {
        let mut data = self.load()?;
        
        let original_len = data.accounts.len();
        data.accounts.retain(|acc| acc.id != id);
        
        if data.accounts.len() == original_len {
            return Err(AccountError::NotFound(id.to_string()));
        }
        
        data.last_sync = Utc::now().to_rfc3339();
        self.save(&data)?;
        Ok(())
    }
    
    pub fn update_account_token(&self, id: &str, token: String) -> Result<Account, AccountError> {
        let mut data = self.load()?;
        
        let account = data.accounts
            .iter_mut()
            .find(|acc| acc.id == id)
            .ok_or_else(|| AccountError::NotFound(id.to_string()))?;
        
        account.token = Some(token);
        account.last_updated = Some(Utc::now().to_rfc3339());
        let result = account.clone();
        data.last_sync = Utc::now().to_rfc3339();
        
        self.save(&data)?;
        Ok(result)
    }
    
    pub fn update_account_quota(&self, id: &str, remaining: i32, total: i32) -> Result<Account, AccountError> {
        let mut data = self.load()?;

        let account = data.accounts
            .iter_mut()
            .find(|acc| acc.id == id)
            .ok_or_else(|| AccountError::NotFound(id.to_string()))?;

        account.quota_remaining = Some(remaining.to_string());
        account.quota_total = Some(total.to_string());
        account.last_updated = Some(Utc::now().to_rfc3339());
        let result = account.clone();
        data.last_sync = Utc::now().to_rfc3339();

        self.save(&data)?;
        Ok(result)
    }
}
