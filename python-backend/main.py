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