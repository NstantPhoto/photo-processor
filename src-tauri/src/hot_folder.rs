use notify::{RecommendedWatcher, RecursiveMode, Watcher};
use notify_debouncer_full::{new_debouncer, DebounceEventResult, Debouncer, FileIdMap};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::{AppHandle, Emitter, State};
use tokio::sync::mpsc;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HotFolderConfig {
    pub id: String,
    pub path: String,
    pub enabled: bool,
    pub extensions: Vec<String>,
    pub stability_timeout: u64, // milliseconds
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WatcherEvent {
    pub event_type: String,
    pub path: String,
    pub folder_id: String,
    pub timestamp: String,
}

pub struct HotFolderManager {
    watchers: Arc<Mutex<HashMap<String, Debouncer<RecommendedWatcher, FileIdMap>>>>,
    configs: Arc<Mutex<HashMap<String, HotFolderConfig>>>,
    app_handle: AppHandle,
}

impl HotFolderManager {
    pub fn new(app_handle: AppHandle) -> Self {
        Self {
            watchers: Arc::new(Mutex::new(HashMap::new())),
            configs: Arc::new(Mutex::new(HashMap::new())),
            app_handle,
        }
    }

    pub fn start_watching(&self, config: HotFolderConfig) -> Result<(), String> {
        let folder_id = config.id.clone();
        let folder_path = config.path.clone();
        let extensions = config.extensions.clone();
        let app_handle = self.app_handle.clone();
        let stability_timeout = Duration::from_millis(config.stability_timeout);

        // Create a channel for events
        let (tx, mut rx) = mpsc::unbounded_channel();

        // Create debounced watcher
        let mut debouncer = new_debouncer(
            stability_timeout,
            None,
            move |result: DebounceEventResult| {
                if let Ok(events) = result {
                    for event in events {
                        let _ = tx.send(event);
                    }
                }
            },
        )
        .map_err(|e| format!("Failed to create watcher: {}", e))?;

        // Add path to watch
        debouncer
            .watcher()
            .watch(Path::new(&folder_path), RecursiveMode::Recursive)
            .map_err(|e| format!("Failed to watch folder: {}", e))?;

        // Store config
        self.configs.lock().unwrap().insert(folder_id.clone(), config);

        // Store watcher
        self.watchers
            .lock()
            .unwrap()
            .insert(folder_id.clone(), debouncer);

        // Spawn task to handle events
        let folder_id_clone = folder_id.clone();
        tokio::spawn(async move {
            while let Some(event) = rx.recv().await {
                if let Some(paths) = event.paths.first() {
                    let path_str = paths.to_string_lossy().to_string();
                    
                    // Check if file has valid extension
                    if let Some(ext) = paths.extension() {
                        let ext_str = ext.to_string_lossy().to_lowercase();
                        if extensions.is_empty() || extensions.contains(&ext_str) {
                            // Emit event to frontend
                            let watcher_event = WatcherEvent {
                                event_type: "file_added".to_string(),
                                path: path_str.clone(),
                                folder_id: folder_id_clone.clone(),
                                timestamp: chrono::Utc::now().to_rfc3339(),
                            };

                            // Send to Python backend
                            let client = reqwest::Client::new();
                            let _ = client
                                .post("http://localhost:8888/queue/add")
                                .json(&serde_json::json!({
                                    "path": path_str,
                                    "folder_id": folder_id_clone,
                                    "priority": "normal"
                                }))
                                .send()
                                .await;

                            // Emit to frontend
                            let _ = app_handle.emit("hot-folder-event", &watcher_event);
                        }
                    }
                }
            }
        });

        Ok(())
    }

    pub fn stop_watching(&self, folder_id: &str) -> Result<(), String> {
        self.watchers.lock().unwrap().remove(folder_id);
        self.configs.lock().unwrap().remove(folder_id);
        Ok(())
    }

    pub fn get_configs(&self) -> Vec<HotFolderConfig> {
        self.configs.lock().unwrap().values().cloned().collect()
    }

    pub fn is_watching(&self, folder_id: &str) -> bool {
        self.watchers.lock().unwrap().contains_key(folder_id)
    }
}

// Tauri commands
#[tauri::command]
pub async fn start_hot_folder(
    config: HotFolderConfig,
    manager: State<'_, Arc<HotFolderManager>>,
) -> Result<(), String> {
    manager.start_watching(config)
}

#[tauri::command]
pub async fn stop_hot_folder(
    folder_id: String,
    manager: State<'_, Arc<HotFolderManager>>,
) -> Result<(), String> {
    manager.stop_watching(&folder_id)
}

#[tauri::command]
pub async fn get_hot_folders(
    manager: State<'_, Arc<HotFolderManager>>,
) -> Result<Vec<HotFolderConfig>, String> {
    Ok(manager.get_configs())
}

#[tauri::command]
pub async fn is_folder_watching(
    folder_id: String,
    manager: State<'_, Arc<HotFolderManager>>,
) -> Result<bool, String> {
    Ok(manager.is_watching(&folder_id))
}