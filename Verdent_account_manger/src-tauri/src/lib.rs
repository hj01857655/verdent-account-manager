mod pkce;
mod storage;
mod api;
mod commands;
mod vscode_storage;
mod account_manager;
mod jwt_utils;
mod settings_manager;

use commands::*;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            login_with_token,
            reset_device_identity,
            reset_all_storage,
            get_storage_info,
            open_vscode_callback,
            get_vscode_ids,
            reset_vscode_ids,
            auto_register_accounts,
            get_all_accounts,
            get_app_data_path,
            get_account,
            update_account,
            delete_account,
            update_account_token,
            update_account_quota,
            login_to_vscode,
            login_to_windsurf,
            login_to_cursor,
            refresh_account_info,
            test_login_and_update,
            import_account_by_token,
            import_account_by_credentials,
            get_user_settings,
            save_user_settings,
            update_current_account,
            update_email_privacy,
            update_selected_accounts,
            update_filter_type,
            update_register_config,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
