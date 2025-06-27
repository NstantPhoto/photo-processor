import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4
from collections import OrderedDict
import time

from pydantic import BaseModel
from enum import Enum


class QueueItemStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class QueueItemPriority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class AddToQueueRequest(BaseModel):
    path: str
    folder_id: str
    priority: QueueItemPriority = QueueItemPriority.NORMAL


class QueueItem(BaseModel):
    id: str
    path: str
    folder_id: str
    status: QueueItemStatus
    priority: QueueItemPriority
    added_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_size: int
    last_modified: datetime
    retry_count: int = 0
    error: Optional[str] = None


class QueueStatus(BaseModel):
    total_items: int
    pending_items: int
    processing_items: int
    completed_items: int
    failed_items: int
    is_paused: bool


class ProcessingQueue:
    def __init__(self):
        self.queue: OrderedDict[str, QueueItem] = OrderedDict()
        self.is_paused = False
        self.processing_lock = asyncio.Lock()
        self.file_stability_timeout = 2.0  # seconds
        self.file_sizes: Dict[str, tuple[int, float]] = {}  # path -> (size, timestamp)
        
    async def add_item(self, request: AddToQueueRequest) -> QueueItem:
        """Add a new item to the queue after checking file stability"""
        path = Path(request.path)
        
        if not path.exists():
            raise ValueError(f"File not found: {request.path}")
        
        # Check if file is stable
        if not await self._is_file_stable(path):
            raise ValueError(f"File is still being written: {request.path}")
        
        # Check if already in queue
        for item in self.queue.values():
            if item.path == request.path and item.status in [QueueItemStatus.PENDING, QueueItemStatus.PROCESSING]:
                return item
        
        # Create new queue item
        stat = path.stat()
        item = QueueItem(
            id=str(uuid4()),
            path=request.path,
            folder_id=request.folder_id,
            status=QueueItemStatus.PENDING,
            priority=request.priority,
            added_at=datetime.utcnow(),
            file_size=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime)
        )
        
        # Add to queue based on priority
        async with self.processing_lock:
            self.queue[item.id] = item
            self._reorder_queue()
        
        return item
    
    async def _is_file_stable(self, path: Path) -> bool:
        """Check if file size has been stable for the required timeout"""
        current_size = path.stat().st_size
        current_time = time.time()
        
        if str(path) in self.file_sizes:
            last_size, last_time = self.file_sizes[str(path)]
            if current_size == last_size:
                if current_time - last_time >= self.file_stability_timeout:
                    # File has been stable
                    del self.file_sizes[str(path)]
                    return True
                else:
                    # Still waiting for stability
                    return False
            else:
                # Size changed, update tracking
                self.file_sizes[str(path)] = (current_size, current_time)
                return False
        else:
            # First time seeing this file
            self.file_sizes[str(path)] = (current_size, current_time)
            return False
    
    def _reorder_queue(self):
        """Reorder queue based on priority and timestamp"""
        priority_order = {
            QueueItemPriority.HIGH: 0,
            QueueItemPriority.NORMAL: 1,
            QueueItemPriority.LOW: 2
        }
        
        # Sort items by status (pending first), then priority, then timestamp
        sorted_items = sorted(
            self.queue.items(),
            key=lambda x: (
                0 if x[1].status == QueueItemStatus.PENDING else 1,
                priority_order[x[1].priority],
                x[1].added_at
            )
        )
        
        self.queue.clear()
        for item_id, item in sorted_items:
            self.queue[item_id] = item
    
    async def get_next_item(self) -> Optional[QueueItem]:
        """Get the next item to process"""
        if self.is_paused:
            return None
        
        async with self.processing_lock:
            for item in self.queue.values():
                if item.status == QueueItemStatus.PENDING:
                    item.status = QueueItemStatus.PROCESSING
                    item.started_at = datetime.utcnow()
                    return item
        
        return None
    
    async def update_item(self, item_id: str, status: QueueItemStatus, error: Optional[str] = None) -> Optional[QueueItem]:
        """Update the status of a queue item"""
        async with self.processing_lock:
            if item_id not in self.queue:
                return None
            
            item = self.queue[item_id]
            item.status = status
            
            if status == QueueItemStatus.COMPLETED:
                item.completed_at = datetime.utcnow()
            elif status == QueueItemStatus.FAILED:
                item.error = error
                item.retry_count += 1
                # Move to end of queue for retry
                self.queue.move_to_end(item_id)
            
            return item
    
    async def remove_item(self, item_id: str) -> bool:
        """Remove an item from the queue"""
        async with self.processing_lock:
            if item_id in self.queue:
                del self.queue[item_id]
                return True
            return False
    
    async def get_status(self) -> QueueStatus:
        """Get current queue status"""
        status_counts = {
            QueueItemStatus.PENDING: 0,
            QueueItemStatus.PROCESSING: 0,
            QueueItemStatus.COMPLETED: 0,
            QueueItemStatus.FAILED: 0
        }
        
        for item in self.queue.values():
            status_counts[item.status] += 1
        
        return QueueStatus(
            total_items=len(self.queue),
            pending_items=status_counts[QueueItemStatus.PENDING],
            processing_items=status_counts[QueueItemStatus.PROCESSING],
            completed_items=status_counts[QueueItemStatus.COMPLETED],
            failed_items=status_counts[QueueItemStatus.FAILED],
            is_paused=self.is_paused
        )
    
    async def get_items(self, limit: int = 100, offset: int = 0) -> List[QueueItem]:
        """Get a paginated list of queue items"""
        items = list(self.queue.values())[offset:offset + limit]
        return items
    
    async def pause(self):
        """Pause queue processing"""
        self.is_paused = True
    
    async def resume(self):
        """Resume queue processing"""
        self.is_paused = False
    
    async def clear(self):
        """Clear all items from the queue"""
        async with self.processing_lock:
            self.queue.clear()


# Global queue instance
processing_queue = ProcessingQueue()