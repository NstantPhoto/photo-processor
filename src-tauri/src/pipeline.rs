use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tauri::State;
use tokio::sync::Mutex;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipelineNode {
    pub id: String,
    pub node_type: String,
    pub processor_type: String,
    pub parameters: HashMap<String, serde_json::Value>,
    pub position: (f32, f32),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipelineConnection {
    pub source: String,
    pub target: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipelineConfig {
    pub nodes: Vec<PipelineNode>,
    pub connections: Vec<PipelineConnection>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessingRequest {
    pub pipeline_config: PipelineConfig,
    pub input_path: String,
    pub output_path: String,
    pub session_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessingResult {
    pub success: bool,
    pub output_path: Option<String>,
    pub processing_time: f64,
    pub quality_score: Option<f64>,
    pub error: Option<String>,
}

pub struct PipelineState {
    pub processing_queue: Mutex<Vec<ProcessingRequest>>,
}

#[tauri::command]
pub async fn execute_pipeline(
    request: ProcessingRequest,
    state: State<'_, PipelineState>,
) -> Result<ProcessingResult, String> {
    // Add to processing queue
    let mut queue = state.processing_queue.lock().await;
    queue.push(request.clone());
    drop(queue);
    
    // Call Python backend to execute pipeline
    let client = reqwest::Client::new();
    let backend_url = "http://localhost:8888/api/pipeline/execute";
    
    let response = client
        .post(backend_url)
        .json(&request)
        .send()
        .await
        .map_err(|e| format!("Failed to connect to backend: {}", e))?;
    
    if response.status().is_success() {
        let result: ProcessingResult = response
            .json()
            .await
            .map_err(|e| format!("Failed to parse response: {}", e))?;
        Ok(result)
    } else {
        Err(format!("Backend error: {}", response.status()))
    }
}

#[tauri::command]
pub async fn get_pipeline_status(
    state: State<'_, PipelineState>,
) -> Result<HashMap<String, serde_json::Value>, String> {
    let queue = state.processing_queue.lock().await;
    let queue_size = queue.len();
    drop(queue);
    
    let mut status = HashMap::new();
    status.insert("queue_size".to_string(), serde_json::json!(queue_size));
    status.insert("backend_connected".to_string(), serde_json::json!(true));
    
    Ok(status)
}

#[tauri::command]
pub async fn save_pipeline_preset(
    name: String,
    config: PipelineConfig,
) -> Result<String, String> {
    // Call Python backend to save preset
    let client = reqwest::Client::new();
    let backend_url = "http://localhost:8888/api/presets/create";
    
    let preset_data = serde_json::json!({
        "name": name,
        "pipeline_config": config,
    });
    
    let response = client
        .post(backend_url)
        .json(&preset_data)
        .send()
        .await
        .map_err(|e| format!("Failed to save preset: {}", e))?;
    
    if response.status().is_success() {
        Ok("Preset saved successfully".to_string())
    } else {
        Err(format!("Failed to save preset: {}", response.status()))
    }
}

#[tauri::command]
pub async fn load_pipeline_preset(name: String) -> Result<PipelineConfig, String> {
    // Call Python backend to load preset
    let client = reqwest::Client::new();
    let backend_url = format!("http://localhost:8888/api/presets/{}", name);
    
    let response = client
        .get(&backend_url)
        .send()
        .await
        .map_err(|e| format!("Failed to load preset: {}", e))?;
    
    if response.status().is_success() {
        let config: PipelineConfig = response
            .json()
            .await
            .map_err(|e| format!("Failed to parse preset: {}", e))?;
        Ok(config)
    } else {
        Err(format!("Failed to load preset: {}", response.status()))
    }
}