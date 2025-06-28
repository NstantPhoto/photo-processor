from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import cv2
import numpy as np
from pathlib import Path
import os
import asyncio
import json

from queue_manager import (
    processing_queue, 
    AddToQueueRequest, 
    QueueItem, 
    QueueStatus,
    QueueItemStatus
)
from pipeline import PipelineManager, ProcessingNode
from processors import (
    ExposureProcessor,
    BrightnessProcessor,
    ColorBalanceProcessor,
    ContrastProcessor,
    QualityAssessmentProcessor
)
from processors.input_processor import InputProcessor, OutputProcessor
from session_manager import SessionManager, SessionType
from preview_manager import PreviewManager, PreviewRequest, PreviewResponse


app = FastAPI(title="Nstant Nfinity Processing Engine", version="0.1.0")

# Configure CORS for Tauri
app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:1420"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ImageInfoRequest(BaseModel):
    path: str


class ImageInfoResponse(BaseModel):
    path: str
    width: int
    height: int
    format: str
    file_size: int


class ProcessRequest(BaseModel):
    path: str
    operations: list[dict]


class HealthResponse(BaseModel):
    status: str
    version: str
    gpu_available: bool


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the processing engine is running"""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        gpu_available=cv2.cuda.getCudaEnabledDeviceCount() > 0
    )


@app.post("/image/info", response_model=ImageInfoResponse)
async def get_image_info(request: ImageInfoRequest):
    """Get information about an image file"""
    path = Path(request.path)
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    
    if not path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Get file size
    file_size = path.stat().st_size
    
    # Read image to get dimensions
    try:
        image = cv2.imread(str(path))
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        height, width = image.shape[:2]
        
        # Determine format from extension
        format_map = {
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.png': 'PNG',
            '.webp': 'WebP',
            '.bmp': 'BMP',
            '.tiff': 'TIFF',
            '.tif': 'TIFF'
        }
        
        ext = path.suffix.lower()
        image_format = format_map.get(ext, ext.upper()[1:])
        
        return ImageInfoResponse(
            path=str(path),
            width=width,
            height=height,
            format=image_format,
            file_size=file_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading image: {str(e)}")


@app.post("/process")
async def process_image(request: ProcessRequest):
    """Process an image with specified operations"""
    # TODO: Implement actual processing pipeline
    # For now, just return success
    return {
        "status": "completed",
        "output_path": request.path,
        "operations_applied": len(request.operations)
    }


# Queue Management Endpoints
@app.post("/queue/add", response_model=QueueItem)
async def add_to_queue(request: AddToQueueRequest):
    """Add a file to the processing queue"""
    try:
        item = await processing_queue.add_item(request)
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/queue/status", response_model=QueueStatus)
async def get_queue_status():
    """Get current queue status"""
    return await processing_queue.get_status()


@app.get("/queue/items", response_model=List[QueueItem])
async def get_queue_items(limit: int = 100, offset: int = 0):
    """Get paginated list of queue items"""
    return await processing_queue.get_items(limit, offset)


@app.get("/queue/next", response_model=Optional[QueueItem])
async def get_next_queue_item():
    """Get the next item to process"""
    return await processing_queue.get_next_item()


@app.put("/queue/item/{item_id}/status")
async def update_queue_item_status(
    item_id: str, 
    status: QueueItemStatus,
    error: Optional[str] = None
):
    """Update the status of a queue item"""
    item = await processing_queue.update_item(item_id, status, error)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return item


@app.delete("/queue/item/{item_id}")
async def remove_queue_item(item_id: str):
    """Remove an item from the queue"""
    removed = await processing_queue.remove_item(item_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return {"status": "removed"}


@app.post("/queue/pause")
async def pause_queue():
    """Pause queue processing"""
    await processing_queue.pause()
    return {"status": "paused"}


@app.post("/queue/resume")
async def resume_queue():
    """Resume queue processing"""
    await processing_queue.resume()
    return {"status": "resumed"}


@app.delete("/queue/clear")
async def clear_queue():
    """Clear all items from the queue"""
    await processing_queue.clear()
    return {"status": "cleared"}


# Pipeline Execution Endpoints
class PipelineNode(BaseModel):
    id: str
    node_type: str
    processor_type: str
    parameters: dict
    position: tuple[float, float]


class PipelineConnection(BaseModel):
    source: str
    target: str


class PipelineConfig(BaseModel):
    nodes: List[PipelineNode]
    connections: List[PipelineConnection]


class ProcessingRequestModel(BaseModel):
    pipeline_config: PipelineConfig
    input_path: str
    output_path: str
    session_id: Optional[str] = None


class ProcessingResult(BaseModel):
    success: bool
    output_path: Optional[str] = None
    processing_time: float
    quality_score: Optional[float] = None
    error: Optional[str] = None


# Initialize managers
pipeline_manager = PipelineManager()
session_manager = SessionManager()
preview_manager = PreviewManager()

# Register processors
pipeline_manager.register_processor('input', InputProcessor)
pipeline_manager.register_processor('output', OutputProcessor)
pipeline_manager.register_processor('exposure', ExposureProcessor)
pipeline_manager.register_processor('brightness', BrightnessProcessor)
pipeline_manager.register_processor('color_balance', ColorBalanceProcessor)
pipeline_manager.register_processor('contrast', ContrastProcessor)
pipeline_manager.register_processor('quality_assessment', QualityAssessmentProcessor)


@app.post("/api/pipeline/execute", response_model=ProcessingResult)
async def execute_pipeline(request: ProcessingRequestModel):
    """Execute a processing pipeline on an image"""
    import time
    start_time = time.time()
    
    try:
        # Clear existing pipeline
        pipeline_manager.nodes.clear()
        pipeline_manager.graph.clear()
        
        # Build pipeline from config
        processor_map = {}
        
        for node in request.pipeline_config.nodes:
            if node.processor_type in pipeline_manager._processor_registry:
                processor_class = pipeline_manager._processor_registry[node.processor_type]
                processor = processor_class()
                processor.set_parameters(**node.parameters)
                
                processing_node = ProcessingNode(
                    id=node.id,
                    processor=processor,
                    position=node.position
                )
                
                pipeline_manager.add_node(processing_node)
                processor_map[node.id] = processing_node
        
        # Add connections
        for conn in request.pipeline_config.connections:
            pipeline_manager.connect_nodes(conn.source, conn.target)
        
        # Validate pipeline
        is_valid, errors = pipeline_manager.validate_pipeline()
        if not is_valid:
            return ProcessingResult(
                success=False,
                error=f"Invalid pipeline: {', '.join(errors)}",
                processing_time=0
            )
        
        # Process image
        input_path = Path(request.input_path)
        output_path = Path(request.output_path)
        
        result = await pipeline_manager.process_image(
            input_path,
            output_path,
            preview_only=False
        )
        
        processing_time = time.time() - start_time
        
        # Get quality score if quality assessment was used
        quality_score = None
        for node in processor_map.values():
            if node.processor.processor_type == 'quality_assessment':
                metrics = node.processor.get_quality_metrics()
                quality_score = metrics.get('score', 0)
                break
        
        # Update session if provided
        if request.session_id:
            session_manager.mark_image_processed(
                request.session_id,
                str(input_path),
                processing_time,
                quality_score
            )
        
        return ProcessingResult(
            success=True,
            output_path=str(output_path),
            processing_time=processing_time,
            quality_score=quality_score
        )
        
    except Exception as e:
        return ProcessingResult(
            success=False,
            error=str(e),
            processing_time=time.time() - start_time
        )


# Session Management Endpoints
@app.get("/api/sessions")
async def get_sessions(status: Optional[str] = None, session_type: Optional[str] = None):
    """Get all sessions"""
    sessions = session_manager.list_sessions(status, SessionType(session_type) if session_type else None)
    return [{"id": s.id, "name": s.name, "date": s.date.isoformat(), "type": s.type.value} for s in sessions]


@app.post("/api/sessions")
async def create_session(session_data: dict):
    """Create a new session"""
    session = session_manager.create_session(
        name=session_data["name"],
        session_type=SessionType(session_data["type"]),
        **{k: v for k, v in session_data.items() if k not in ["name", "type"]}
    )
    return {"id": session.id}


# Preset Management Endpoints
@app.post("/api/presets/create")
async def create_preset(preset_data: dict):
    """Create a new processing preset"""
    preset = session_manager.create_preset(
        name=preset_data["name"],
        pipeline_config=preset_data["pipeline_config"]
    )
    return {"id": preset.id}


@app.get("/api/presets")
async def get_presets():
    """Get all presets"""
    presets = session_manager.list_presets()
    return [{"id": p.id, "name": p.name, "tags": p.tags} for p in presets]


# Preview Generation Endpoints
@app.post("/api/preview/generate", response_model=PreviewResponse)
async def generate_preview(request: PreviewRequest):
    """Generate a preview for an image"""
    try:
        response = await preview_manager.generate_preview(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/preview/thumbnail")
async def generate_thumbnail(image_path: str, size: int = 150):
    """Generate a thumbnail for an image"""
    try:
        thumbnail_path = await preview_manager.generate_thumbnail(image_path, size)
        return {"thumbnail_path": thumbnail_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/preview/cache/stats")
async def get_cache_stats():
    """Get preview cache statistics"""
    return preview_manager.get_cache_stats()


@app.delete("/api/preview/cache")
async def clear_preview_cache(older_than_days: Optional[int] = None):
    """Clear preview cache"""
    preview_manager.clear_cache(older_than_days)
    return {"status": "cache cleared"}


# Server-Sent Events for real-time updates
@app.get("/queue/events")
async def queue_events():
    """Stream queue status updates via Server-Sent Events"""
    async def event_generator():
        while True:
            status = await processing_queue.get_status()
            yield f"data: {json.dumps(status.dict())}\n\n"
            await asyncio.sleep(1)  # Update every second
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8888, reload=True)