#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod hot_folder;

use commands::{get_image_info, process_image, check_backend_health};
use hot_folder::{start_hot_folder, stop_hot_folder, get_hot_folders, is_folder_watching, HotFolderManager};
use std::sync::Arc;
use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let hot_folder_manager = Arc::new(HotFolderManager::new(app.handle().clone()));
            app.manage(hot_folder_manager);
            Ok(())
        })
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            get_image_info,
            process_image,
            check_backend_health,
            start_hot_folder,
            stop_hot_folder,
            get_hot_folders,
            is_folder_watching
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}