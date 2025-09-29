"""
Data models for Contextualize
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, TypeVar, Generic, Protocol
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod


T = TypeVar("T")


class CollectionMixin(ABC, Generic[T]):
    """Mixin for collections with common operations"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._items: Dict[str, T] = {}
        self._loaded = False

    @classmethod
    def from_path(cls, path: Path):
        """Create collection from a specific path"""
        return cls(base_dir=path)

    @abstractmethod
    def _load_item(self, path: Path) -> Optional[T]:
        """Load a single item from path"""
        pass

    @abstractmethod
    def _get_item_id(self, item: T) -> str:
        """Get ID from item"""
        pass

    def load(self, force_reload: bool = False) -> Dict[str, T]:
        """Load all items from filesystem"""
        if self._loaded and not force_reload:
            return self._items

        self._items = {}

        if not self.base_dir.exists():
            self._loaded = True
            return self._items

        # Load items
        for item_path in self.base_dir.iterdir():
            if self._is_valid_path(item_path):
                item = self._load_item(item_path)
                if item:
                    self._items[self._get_item_id(item)] = item

        self._loaded = True
        return self._items

    def _is_valid_path(self, path: Path) -> bool:
        """Check if path should be loaded"""
        return not path.name.startswith(".")

    def get(self, item_id: str, partial: bool = True) -> Optional[T]:
        """Get item by ID (supports partial matching)"""
        self.load()

        # Try exact match first
        if item_id in self._items:
            return self._items[item_id]

        # Try partial match
        if partial:
            matches = [iid for iid in self._items if iid.startswith(item_id)]
            if len(matches) == 1:
                return self._items[matches[0]]

        return None

    def list(self, limit: Optional[int] = None) -> List[T]:
        """List all items with optional limit"""
        self.load()
        items = list(self._items.values())

        if limit:
            items = items[:limit]

        return items

    def count(self) -> int:
        """Count total items"""
        self.load()
        return len(self._items)

    def exists(self, item_id: str) -> bool:
        """Check if item exists"""
        return self.get(item_id) is not None


class TaskStatus(Enum):
    """Task status enumeration"""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REPORTING = "reporting"
    REPORTED = "reported"


@dataclass
class Task:
    """Individual task representation"""

    # Core properties
    task_id: str
    description: str
    status: TaskStatus = TaskStatus.CREATED

    # Context
    concepts: List[str] = field(default_factory=list)
    context_from_main: str = ""

    # Relationships
    parent_id: Optional[str] = None

    # Session management
    session_id: Optional[str] = None

    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Process info
    pid: Optional[int] = None

    # Directory reference
    task_dir: Optional[Path] = None

    # Report configuration
    report_template: Optional[str] = "context/reports/default.md"
    report_status: Optional[str] = None  # pending, generating, completed, failed
    report_generated_at: Optional[datetime] = None
    report_session_id: Optional[str] = None

    @classmethod
    def from_dir(cls, task_dir: Path) -> Optional["Task"]:
        """Load task from directory"""
        metadata_file = task_dir / "metadata.json"
        if not metadata_file.exists():
            return None

        with open(metadata_file) as f:
            data = json.load(f)

        # Convert status string to enum
        status = TaskStatus(data.get("status", "created"))

        # Parse timestamps
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])

        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])

        return cls(
            task_id=data["task_id"],
            description=data.get("description", ""),
            status=status,
            concepts=data.get("concepts", []),
            context_from_main=data.get("context_from_main", ""),
            parent_id=data.get("parent_id"),
            session_id=data.get("session_id"),
            started_at=started_at,
            completed_at=completed_at,
            pid=data.get("pid"),
            task_dir=task_dir,
        )

    def save(self, task_dir: Optional[Path] = None):
        """Save task metadata to directory"""
        if task_dir:
            self.task_dir = task_dir
        if not self.task_dir:
            raise ValueError("No task directory specified")

        self.task_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status.value,
            "concepts": self.concepts,
            "context_from_main": self.context_from_main,
            "parent_id": self.parent_id,
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "pid": self.pid,
        }

        metadata_file = self.task_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))

    def get_output(self) -> Optional[str]:
        """Get task output if exists"""
        if not self.task_dir:
            return None

        output_file = self.task_dir / "output.txt"
        if output_file.exists():
            return output_file.read_text()
        return None

    def get_error(self) -> Optional[str]:
        """Get task error if exists"""
        if not self.task_dir:
            return None

        error_file = self.task_dir / "error.txt"
        if error_file.exists():
            return error_file.read_text()
        return None

    def get_input(self) -> Optional[Dict[str, Any]]:
        """Get task input data"""
        if not self.task_dir:
            return None

        input_file = self.task_dir / "input.json"
        if input_file.exists():
            with open(input_file) as f:
                return json.load(f)
        return None

    def is_running(self) -> bool:
        """Check if task is still running"""
        if self.status != TaskStatus.RUNNING:
            return False

        # Check PID if available
        if self.pid:
            import os

            try:
                os.kill(self.pid, 0)
                return True
            except ProcessLookupError:
                return False

        return self.status == TaskStatus.RUNNING

    def update_status(self, new_status: TaskStatus):
        """Update task status and save"""
        self.status = new_status
        if new_status == TaskStatus.COMPLETED or new_status == TaskStatus.FAILED:
            self.completed_at = datetime.now()
        self.save()

    def remove(self):
        """Remove task directory and files"""
        if self.task_dir and self.task_dir.exists():
            shutil.rmtree(self.task_dir)


class TaskCollection:
    """Collection of tasks with management methods"""

    def __init__(self, logs_dir: Path = Path("logs")):
        self.logs_dir = logs_dir
        self.dag_file = logs_dir / "dag.jsonl"
        self._tasks: Dict[str, Task] = {}
        self._loaded = False

    @classmethod
    def from_path(cls, path: Path) -> "TaskCollection":
        """Create TaskCollection from a specific path"""
        return cls(logs_dir=path)

    def load(self, force_reload: bool = False) -> Dict[str, Task]:
        """Load all tasks from filesystem"""
        if self._loaded and not force_reload:
            return self._tasks

        self._tasks = {}

        if not self.logs_dir.exists():
            self._loaded = True
            return self._tasks

        # Load from directories
        for task_dir in self.logs_dir.iterdir():
            if task_dir.is_dir() and not task_dir.name.startswith("."):
                task = Task.from_dir(task_dir)
                if task:
                    self._tasks[task.task_id] = task

        self._loaded = True
        return self._tasks

    def get(self, task_id: str, partial: bool = True) -> Optional[Task]:
        """Get task by ID (supports partial matching)"""
        self.load()

        # Try exact match first
        if task_id in self._tasks:
            return self._tasks[task_id]

        # Try partial match
        if partial:
            matches = [tid for tid in self._tasks if tid.startswith(task_id)]
            if len(matches) == 1:
                return self._tasks[matches[0]]

        return None

    def list(
        self,
        limit: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        parent_id: Optional[str] = None,
    ) -> List[Task]:
        """List tasks with optional filters"""
        self.load()

        tasks = list(self._tasks.values())

        # Apply filters
        if status:
            tasks = [t for t in tasks if t.status == status]

        if parent_id:
            tasks = [t for t in tasks if t.parent_id == parent_id]

        # Sort by start time (newest first)
        tasks.sort(key=lambda t: t.started_at or datetime.min, reverse=True)

        # Apply limit
        if limit:
            tasks = tasks[:limit]

        return tasks

    def add(self, task: Task) -> Task:
        """Add new task to collection"""
        # Save to filesystem
        task_dir = self.logs_dir / task.task_id
        task.save(task_dir)

        # Add to memory
        self._tasks[task.task_id] = task

        # Log to DAG
        self._log_to_dag(task)

        return task

    def remove(self, task_id: str, partial: bool = True) -> bool:
        """Remove task by ID"""
        task = self.get(task_id, partial=partial)
        if not task:
            return False

        # Remove from filesystem
        task.remove()

        # Remove from memory
        if task.task_id in self._tasks:
            del self._tasks[task.task_id]

        return True

    def clear(self, force: bool = False) -> int:
        """Clear all tasks"""
        self.load()
        count = len(self._tasks)

        if not force and count > 0:
            # Should be confirmed by caller
            raise ValueError(f"Clearing {count} tasks requires force=True")

        # Remove all task directories
        for task in self._tasks.values():
            task.remove()

        # Clear DAG file
        if self.dag_file.exists():
            self.dag_file.unlink()

        # Clear memory
        self._tasks = {}

        return count

    def get_children(self, parent_id: str) -> List[Task]:
        """Get all tasks forked from a parent"""
        return self.list(parent_id=parent_id)

    def get_tree(self, root_id: Optional[str] = None) -> Dict[str, Any]:
        """Build task tree structure"""
        self.load()

        if root_id:
            root = self.get(root_id)
            if not root:
                return {}

            return self._build_tree_node(root)
        else:
            # Find all root tasks (no parent)
            roots = [t for t in self._tasks.values() if not t.parent_id]
            return {"roots": [self._build_tree_node(r) for r in roots]}

    def _build_tree_node(self, task: Task) -> Dict[str, Any]:
        """Build tree node for a task"""
        children = self.get_children(task.task_id)

        return {"task": task, "children": [self._build_tree_node(c) for c in children]}

    def update_running_tasks(self):
        """Update status of running tasks based on PID"""
        self.load()

        for task in self._tasks.values():
            if task.is_running():
                # Check if actually still running
                if task.pid:
                    import os

                    try:
                        os.kill(task.pid, 0)
                    except ProcessLookupError:
                        # Process finished
                        task.update_status(TaskStatus.COMPLETED)

    def get_dag_entries(self) -> List[Dict[str, Any]]:
        """Get all DAG entries"""
        if not self.dag_file.exists():
            return []

        entries = []
        with open(self.dag_file) as f:
            for line in f:
                entries.append(json.loads(line))

        return entries

    def _log_to_dag(self, task: Task):
        """Append task to DAG log"""
        entry = {
            "task_id": task.task_id,
            "description": task.description,
            "status": task.status.value,
            "parent_id": task.parent_id,
            "timestamp": (task.started_at or datetime.now()).isoformat(),
        }

        with open(self.dag_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def stats(self) -> Dict[str, int]:
        """Get collection statistics"""
        self.load()

        return {
            "total": len(self._tasks),
            "created": len([t for t in self._tasks.values() if t.status == TaskStatus.CREATED]),
            "running": len([t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]),
            "completed": len([t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in self._tasks.values() if t.status == TaskStatus.FAILED]),
            "with_parent": len([t for t in self._tasks.values() if t.parent_id]),
        }


# Usage example:
if __name__ == "__main__":
    # Create collection
    tasks = TaskCollection()

    # Load all tasks
    tasks.load()

    # Get specific task
    task = tasks.get("abc123")  # Supports partial IDs

    # List recent completed tasks
    completed = tasks.list(limit=10, status=TaskStatus.COMPLETED)

    # Clear all tasks (with confirmation)
    # tasks.clear(force=True)

    # Get stats
    stats = tasks.stats()
    print(f"Total tasks: {stats['total']}")
    print(f"Running: {stats['running']}")
    print(f"Completed: {stats['completed']}")
