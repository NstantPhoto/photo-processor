import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import uuid
from queue import PriorityQueue
import threading
import logging


logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Status of a processing job"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(Enum):
    """Processing priority levels"""
    LOW = 3
    MEDIUM = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class QueueItem:
    """Item in the processing queue"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input_path: Path = None
    output_path: Optional[Path] = None
    priority: Priority = Priority.MEDIUM
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    pipeline_config: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """Compare items by priority then by creation time"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at


class ProcessingQueue:
    """
    Manages the queue of images to be processed.
    Handles prioritization, batching, and error recovery.
    """
    
    def __init__(self, max_workers: int = 4, max_queue_size: int = 1000):
        """
        Initialize the processing queue.
        
        Args:
            max_workers: Maximum number of concurrent workers
            max_queue_size: Maximum number of items in queue
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # Thread-safe priority queue
        self._queue = PriorityQueue(maxsize=max_queue_size)
        
        # Track active jobs
        self._active_jobs: Dict[str, QueueItem] = {}
        self._completed_jobs: Dict[str, QueueItem] = {}
        self._failed_jobs: Dict[str, QueueItem] = {}
        
        # Callbacks
        self._on_progress: Optional[Callable] = None
        self._on_complete: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
        
        # Thread management
        self._workers: List[threading.Thread] = []
        self._shutdown = threading.Event()
        self._lock = threading.Lock()
        
        # Stats
        self._total_processed = 0
        self._total_failed = 0
        
    def start(self):
        """Start worker threads."""
        logger.info(f"Starting processing queue with {self.max_workers} workers")
        
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"ProcessingWorker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
    
    def stop(self, timeout: float = 30.0):
        """Stop all workers gracefully."""
        logger.info("Stopping processing queue")
        self._shutdown.set()
        
        # Wait for workers to finish
        for worker in self._workers:
            worker.join(timeout=timeout)
        
        self._workers.clear()
    
    def add_item(self, item: QueueItem) -> bool:
        """
        Add an item to the processing queue.
        
        Args:
            item: Item to add to queue
            
        Returns:
            True if added successfully, False if queue is full
        """
        try:
            self._queue.put_nowait((item.priority.value, item))
            logger.debug(f"Added item {item.id} to queue with priority {item.priority.name}")
            return True
        except:
            logger.warning(f"Queue is full, cannot add item {item.id}")
            return False
    
    def add_batch(self, paths: List[Path], priority: Priority = Priority.MEDIUM,
                  session_id: Optional[str] = None, **kwargs) -> List[str]:
        """
        Add multiple items to the queue.
        
        Args:
            paths: List of input paths
            priority: Priority for all items
            session_id: Session ID for grouping
            **kwargs: Additional metadata
            
        Returns:
            List of item IDs that were added
        """
        added_ids = []
        
        for path in paths:
            item = QueueItem(
                input_path=path,
                priority=priority,
                session_id=session_id,
                metadata=kwargs
            )
            
            if self.add_item(item):
                added_ids.append(item.id)
        
        logger.info(f"Added {len(added_ids)} items to queue")
        return added_ids
    
    def cancel_item(self, item_id: str) -> bool:
        """
        Cancel a pending item.
        
        Args:
            item_id: ID of item to cancel
            
        Returns:
            True if cancelled, False if not found or already processing
        """
        with self._lock:
            # Check if actively processing
            if item_id in self._active_jobs:
                # Mark for cancellation
                self._active_jobs[item_id].status = ProcessingStatus.CANCELLED
                return True
        
        # Try to remove from queue
        temp_items = []
        cancelled = False
        
        while not self._queue.empty():
            priority, item = self._queue.get()
            if item.id == item_id:
                item.status = ProcessingStatus.CANCELLED
                cancelled = True
            else:
                temp_items.append((priority, item))
        
        # Put items back
        for priority_item in temp_items:
            self._queue.put(priority_item)
        
        return cancelled
    
    def get_status(self, item_id: str) -> Optional[QueueItem]:
        """Get status of a specific item."""
        with self._lock:
            # Check active jobs
            if item_id in self._active_jobs:
                return self._active_jobs[item_id]
            
            # Check completed jobs
            if item_id in self._completed_jobs:
                return self._completed_jobs[item_id]
            
            # Check failed jobs
            if item_id in self._failed_jobs:
                return self._failed_jobs[item_id]
        
        # Check queue
        temp_items = []
        found_item = None
        
        while not self._queue.empty():
            priority, item = self._queue.get()
            if item.id == item_id:
                found_item = item
            temp_items.append((priority, item))
        
        # Put items back
        for priority_item in temp_items:
            self._queue.put(priority_item)
        
        return found_item
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            return {
                'pending': self._queue.qsize(),
                'active': len(self._active_jobs),
                'completed': len(self._completed_jobs),
                'failed': len(self._failed_jobs),
                'total_processed': self._total_processed,
                'total_failed': self._total_failed,
                'workers': self.max_workers
            }
    
    def get_session_items(self, session_id: str) -> List[QueueItem]:
        """Get all items for a session."""
        items = []
        
        with self._lock:
            # Check all job collections
            for collection in [self._active_jobs, self._completed_jobs, self._failed_jobs]:
                for item in collection.values():
                    if item.session_id == session_id:
                        items.append(item)
        
        # Check queue
        temp_items = []
        while not self._queue.empty():
            priority, item = self._queue.get()
            if item.session_id == session_id:
                items.append(item)
            temp_items.append((priority, item))
        
        # Put items back
        for priority_item in temp_items:
            self._queue.put(priority_item)
        
        return items
    
    def set_callbacks(self, on_progress: Optional[Callable] = None,
                     on_complete: Optional[Callable] = None,
                     on_error: Optional[Callable] = None):
        """Set callback functions."""
        self._on_progress = on_progress
        self._on_complete = on_complete
        self._on_error = on_error
    
    def _worker_loop(self):
        """Main worker loop."""
        while not self._shutdown.is_set():
            try:
                # Get item from queue with timeout
                priority, item = self._queue.get(timeout=1.0)
                
                # Check if cancelled
                if item.status == ProcessingStatus.CANCELLED:
                    continue
                
                # Process item
                self._process_item(item)
                
            except:
                # Queue is empty or timeout, continue
                continue
    
    def _process_item(self, item: QueueItem):
        """Process a single queue item."""
        # Mark as active
        with self._lock:
            item.status = ProcessingStatus.PROCESSING
            item.started_at = datetime.now()
            self._active_jobs[item.id] = item
        
        try:
            # Update progress callback
            if self._on_progress:
                self._on_progress(item)
            
            # Simulate processing (will be replaced with actual pipeline call)
            import time
            for i in range(101):
                if self._shutdown.is_set() or item.status == ProcessingStatus.CANCELLED:
                    break
                
                item.progress = i / 100.0
                if self._on_progress and i % 10 == 0:
                    self._on_progress(item)
                
                time.sleep(0.01)  # Simulate work
            
            # Mark as completed
            with self._lock:
                item.status = ProcessingStatus.COMPLETED
                item.completed_at = datetime.now()
                item.progress = 1.0
                
                del self._active_jobs[item.id]
                self._completed_jobs[item.id] = item
                self._total_processed += 1
            
            # Completion callback
            if self._on_complete:
                self._on_complete(item)
                
        except Exception as e:
            # Mark as failed
            with self._lock:
                item.status = ProcessingStatus.FAILED
                item.error = str(e)
                item.completed_at = datetime.now()
                
                del self._active_jobs[item.id]
                self._failed_jobs[item.id] = item
                self._total_failed += 1
            
            # Error callback
            if self._on_error:
                self._on_error(item, e)
            
            logger.error(f"Failed to process item {item.id}: {e}")
    
    def clear_completed(self):
        """Clear completed and failed jobs from memory."""
        with self._lock:
            self._completed_jobs.clear()
            self._failed_jobs.clear()
    
    def retry_failed(self) -> List[str]:
        """Retry all failed jobs."""
        retry_ids = []
        
        with self._lock:
            for item in list(self._failed_jobs.values()):
                # Reset item status
                item.status = ProcessingStatus.PENDING
                item.error = None
                item.progress = 0.0
                item.started_at = None
                item.completed_at = None
                
                # Add back to queue
                if self.add_item(item):
                    retry_ids.append(item.id)
                    del self._failed_jobs[item.id]
        
        logger.info(f"Retrying {len(retry_ids)} failed items")
        return retry_ids