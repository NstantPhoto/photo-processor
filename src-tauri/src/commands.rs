use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Serialize, Deserialize)]
pub struct ImageInfo {
    path: String,
    width: u32,
    height: u32,
    format: String,
    file_size: u64,
}

#[derive(Serialize)]
struct ImageInfoRequest {
    path: String,
}

#[tauri::command]
pub async fn get_image_info(path: String) -> Result<ImageInfo, String> {
    // Validate path exists
    let path_obj = Path::new(&path);
    if !path_obj.exists() {
        return Err("File not found".to_string());
    }

    // Call Python backend
    let client = reqwest::Client::new();
    let request = ImageInfoRequest { path: path.clone() };
    
    let response = client
        .post("http://localhost:8888/image/info")
        .json(&request)
        .send()
        .await
        .map_err(|e| format!("Failed to connect to processing engine: {}", e))?;
    
    if !response.status().is_success() {
        let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
        return Err(format!("Processing engine error: {}", error_text));
    }
    
    let image_info = response
        .json::<ImageInfo>()
        .await
        .map_err(|e| format!("Invalid response from processing engine: {}", e))?;
    
    Ok(image_info)
}

#[derive(Deserialize)]
struct HealthResponse {
    status: String,
    version: String,
    gpu_available: bool,
}

#[tauri::command]
pub async fn check_backend_health() -> Result<bool, String> {
    let client = reqwest::Client::new();
    
    match client.get("http://localhost:8888/health").send().await {
        Ok(response) => {
            if response.status().is_success() {
                match response.json::<HealthResponse>().await {
                    Ok(health) => Ok(health.status == "healthy"),
                    Err(_) => Ok(false),
                }
            } else {
                Ok(false)
            }
        }
        Err(_) => Ok(false),
    }
}

#[tauri::command]
pub async fn process_image(path: String) -> Result<String, String> {
    // TODO: Call Python backend for processing
    // For now, just return the same path
    Ok(path)
}