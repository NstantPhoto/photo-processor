#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod hot_folder;
mod pipeline;

use commands::{get_image_info, process_image, check_backend_health, generate_preview, generate_thumbnail};
use hot_folder::{start_hot_folder, stop_hot_folder, get_hot_folders, is_folder_watching, HotFolderManager};
use pipeline::{execute_pipeline, get_pipeline_status, save_pipeline_preset, load_pipeline_preset, PipelineState};
use std::sync::Arc;
use tauri::Manager;
use tokio::sync::Mutex;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let hot_folder_manager = Arc::new(HotFolderManager::new(app.handle().clone()));
            app.manage(hot_folder_manager);
            
            let pipeline_state = PipelineState {
                processing_queue: Mutex::new(Vec::new()),
            };
            app.manage(pipeline_state);
            
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
            is_folder_watching,
            execute_pipeline,
            get_pipeline_status,
            save_pipeline_preset,
            load_pipeline_preset,
            generate_preview,
            generate_thumbnail
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}