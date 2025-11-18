use std::process::Command;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

#[cfg(target_os = "windows")]
const CREATE_NO_WINDOW: u32 = 0x08000000;

/// 检查当前进程是否以管理员权限运行
#[cfg(target_os = "windows")]
pub fn is_running_as_admin() -> bool {
    use windows::Win32::Foundation::HANDLE;
    use windows::Win32::Security::{
        GetTokenInformation, TokenElevation, TOKEN_ELEVATION, TOKEN_QUERY,
    };
    use windows::Win32::System::Threading::{GetCurrentProcess, OpenProcessToken};

    unsafe {
        let mut token: HANDLE = HANDLE::default();

        // 打开当前进程的访问令牌
        if OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &mut token).is_err() {
            println!("[!] 无法打开进程令牌");
            return false;
        }

        let mut elevation = TOKEN_ELEVATION { TokenIsElevated: 0 };
        let mut return_length: u32 = 0;

        // 查询令牌的提升状态
        let result = GetTokenInformation(
            token,
            TokenElevation,
            Some(&mut elevation as *mut _ as *mut _),
            std::mem::size_of::<TOKEN_ELEVATION>() as u32,
            &mut return_length,
        );

        if result.is_err() {
            println!("[!] 无法获取令牌信息");
            return false;
        }

        let is_admin = elevation.TokenIsElevated != 0;
        println!("[*] 管理员权限检查: {}", if is_admin { "是" } else { "否" });

        is_admin
    }
}

#[cfg(not(target_os = "windows"))]
pub fn is_running_as_admin() -> bool {
    // 在非 Windows 平台上，总是返回 true（不需要特殊权限）
    true
}

/// 重新启动应用程序并请求管理员权限
#[cfg(target_os = "windows")]
pub fn restart_as_admin() -> Result<(), String> {
    use std::env;
    
    let exe_path = env::current_exe()
        .map_err(|e| format!("获取程序路径失败: {}", e))?;
    
    // 使用 PowerShell 来启动具有管理员权限的进程
    let ps_command = format!(
        "Start-Process -FilePath '{}' -Verb RunAs",
        exe_path.display()
    );
    
    let output = Command::new("powershell")
        .args(&["-WindowStyle", "Hidden", "-Command", &ps_command])
        .creation_flags(CREATE_NO_WINDOW)
        .output()
        .map_err(|e| format!("启动 PowerShell 失败: {}", e))?;
    
    if output.status.success() {
        // 成功启动新进程，退出当前进程
        std::process::exit(0);
    } else {
        Err(format!("请求管理员权限失败: {}", 
            String::from_utf8_lossy(&output.stderr)))
    }
}

#[cfg(not(target_os = "windows"))]
pub fn restart_as_admin() -> Result<(), String> {
    Err("非 Windows 平台不支持此功能".to_string())
}

/// 执行需要管理员权限的操作
/// 如果当前没有管理员权限，会尝试获取
pub fn execute_with_admin<F>(operation: F) -> Result<(), String>
where
    F: FnOnce() -> Result<(), String>,
{
    if is_running_as_admin() {
        // 已经有管理员权限，直接执行
        operation()
    } else {
        // 尝试获取管理员权限
        println!("[!] 需要管理员权限来执行此操作");
        restart_as_admin()
    }
}

/// 创建 Windows 任务计划，使应用在启动时自动以管理员权限运行
#[cfg(target_os = "windows")]
pub fn create_admin_task(task_name: &str) -> Result<(), String> {
    let exe_path = std::env::current_exe()
        .map_err(|e| format!("获取程序路径失败: {}", e))?;
    
    // 创建任务计划的 PowerShell 脚本
    let ps_script = format!(
        r#"
        $Action = New-ScheduledTaskAction -Execute "{}"
        $Trigger = New-ScheduledTaskTrigger -AtLogon
        $Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -RunLevel Highest
        $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        
        Register-ScheduledTask -TaskName "{}" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force
        "#,
        exe_path.display(),
        task_name
    );
    
    let output = Command::new("powershell")
        .args(&["-ExecutionPolicy", "Bypass", "-Command", &ps_script])
        .creation_flags(CREATE_NO_WINDOW)
        .output()
        .map_err(|e| format!("执行 PowerShell 失败: {}", e))?;
    
    if !output.status.success() {
        return Err(format!(
            "创建任务计划失败: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }
    
    Ok(())
}

/// 删除任务计划
#[cfg(target_os = "windows")]
pub fn remove_admin_task(task_name: &str) -> Result<(), String> {
    let output = Command::new("schtasks")
        .args(&["/Delete", "/TN", task_name, "/F"])
        .creation_flags(CREATE_NO_WINDOW)
        .output()
        .map_err(|e| format!("删除任务计划失败: {}", e))?;
    
    if !output.status.success() {
        return Err(format!(
            "删除任务计划失败: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }
    
    Ok(())
}

/// 通过任务计划启动应用（以管理员权限）
#[cfg(target_os = "windows")]
pub fn run_via_task(task_name: &str) -> Result<(), String> {
    let output = Command::new("schtasks")
        .args(&["/Run", "/TN", task_name])
        .creation_flags(CREATE_NO_WINDOW)
        .output()
        .map_err(|e| format!("运行任务失败: {}", e))?;
    
    if !output.status.success() {
        return Err(format!(
            "运行任务失败: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }
    
    Ok(())
}
