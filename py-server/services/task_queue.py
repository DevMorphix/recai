"""
Task Queue for managing long-running AI tasks.
Prevents server overload and enables progress tracking.
"""

import threading
import queue
import uuid
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    id: str
    task_type: str
    params: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    progress_message: str = ""
    result: Any = None
    error: str = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_type': self.task_type,
            'status': self.status.value,
            'progress': self.progress,
            'progress_message': self.progress_message,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'duration': (self.completed_at - self.started_at) if self.completed_at and self.started_at else None
        }


class TaskQueue:
    """
    Thread-safe task queue for AI processing.
    
    Features:
    - Single worker thread (prevents GPU memory issues)
    - Progress tracking
    - Task status polling
    - Automatic cleanup of old tasks
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        # Singleton pattern
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._queue = queue.Queue()
        self._tasks: Dict[str, Task] = {}
        self._handlers: Dict[str, Callable] = {}
        self._worker_thread = None
        self._running = False
        self._current_task_id = None
        self._max_tasks = 100  # Max stored tasks
        self._task_ttl = 3600  # 1 hour TTL for completed tasks
        self._initialized = True
        
        logger.info("TaskQueue initialized")
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register a handler function for a task type."""
        self._handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    def start(self):
        """Start the worker thread."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        logger.info("TaskQueue worker started")
    
    def stop(self):
        """Stop the worker thread."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("TaskQueue worker stopped")
    
    def submit(self, task_type: str, params: Dict[str, Any]) -> str:
        """Submit a new task and return its ID."""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            task_type=task_type,
            params=params
        )
        
        self._tasks[task_id] = task
        self._queue.put(task_id)
        
        # Cleanup old tasks
        self._cleanup_old_tasks()
        
        logger.info(f"Task submitted: {task_id} ({task_type})")
        return task_id
    
    def get_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a task."""
        task = self._tasks.get(task_id)
        if task:
            return task.to_dict()
        return None
    
    def get_result(self, task_id: str) -> Optional[Any]:
        """Get the result of a completed task."""
        task = self._tasks.get(task_id)
        if task and task.status == TaskStatus.COMPLETED:
            return task.result
        return None
    
    def cancel(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self._tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            logger.info(f"Task cancelled: {task_id}")
            return True
        return False
    
    def get_queue_info(self) -> Dict:
        """Get queue statistics."""
        pending = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)
        processing = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PROCESSING)
        completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)
        
        return {
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed,
            'total': len(self._tasks),
            'current_task': self._current_task_id,
            'queue_size': self._queue.qsize()
        }
    
    def update_progress(self, task_id: str, progress: int, message: str = ""):
        """Update task progress (called by handlers)."""
        task = self._tasks.get(task_id)
        if task:
            task.progress = progress
            task.progress_message = message
    
    def _worker(self):
        """Worker thread that processes tasks."""
        while self._running:
            try:
                # Get task with timeout (allows checking _running flag)
                try:
                    task_id = self._queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                task = self._tasks.get(task_id)
                if not task or task.status == TaskStatus.CANCELLED:
                    continue
                
                self._current_task_id = task_id
                task.status = TaskStatus.PROCESSING
                task.started_at = time.time()
                
                logger.info(f"Processing task: {task_id} ({task.task_type})")
                
                try:
                    handler = self._handlers.get(task.task_type)
                    if handler:
                        # Pass task_id for progress updates
                        result = handler(task.params, task_id, self)
                        task.result = result
                        task.status = TaskStatus.COMPLETED
                        task.progress = 100
                        logger.info(f"Task completed: {task_id}")
                    else:
                        raise ValueError(f"No handler for task type: {task.task_type}")
                        
                except Exception as e:
                    logger.error(f"Task failed: {task_id} - {str(e)}")
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                
                finally:
                    task.completed_at = time.time()
                    self._current_task_id = None
                    
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
    
    def _cleanup_old_tasks(self):
        """Remove old completed/failed tasks."""
        if len(self._tasks) <= self._max_tasks:
            return
        
        now = time.time()
        to_remove = []
        
        for task_id, task in self._tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                if task.completed_at and (now - task.completed_at) > self._task_ttl:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._tasks[task_id]
            
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old tasks")


# Global queue instance
task_queue = TaskQueue()
