"""Task scheduler with dependency resolution."""

from typing import List, Set, Dict, Optional
from dataclasses import dataclass

from .logger import logger
from .tasks import Task, TaskGraph


@dataclass
class ScheduledTask:
    """A task with scheduling information."""
    task: Task
    level: int  # Dependency level (0 = no deps, higher = more deps)
    ready: bool = False


class TaskScheduler:
    """Schedules tasks respecting dependencies and priorities."""
    
    def __init__(self, task_graph: TaskGraph):
        """
        Initialize scheduler with task graph.
        
        Args:
            task_graph: Graph of tasks with dependencies
        """
        self.task_graph = task_graph
        self.completed: Set[str] = set()
        self.in_progress: Set[str] = set()
        self.failed: Set[str] = set()
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        
        self._compute_dependency_levels()
    
    def _compute_dependency_levels(self) -> None:
        """Compute dependency level for each task (topological ordering)."""
        levels: Dict[str, int] = {}
        
        def compute_level(task_id: str) -> int:
            """Recursively compute dependency level."""
            if task_id in levels:
                return levels[task_id]
            
            task = self.task_graph.get_task(task_id)
            if not task:
                levels[task_id] = 0
                return 0
            
            if not task.deps:
                levels[task_id] = 0
                return 0
            
            max_dep_level = 0
            for dep_id in task.deps:
                dep_level = compute_level(dep_id)
                max_dep_level = max(max_dep_level, dep_level)
            
            levels[task_id] = max_dep_level + 1
            return levels[task_id]
        
        for task in self.task_graph.tasks:
            level = compute_level(task.id)
            self.scheduled_tasks[task.id] = ScheduledTask(
                task=task,
                level=level,
                ready=len(task.deps) == 0
            )
    
    def get_next_batch(self, batch_size: int) -> List[Task]:
        """
        Get next batch of tasks to execute.
        
        Args:
            batch_size: Maximum number of tasks to return
            
        Returns:
            List of tasks ready to execute
        """
        ready_tasks = []
        
        for scheduled in self.scheduled_tasks.values():
            task = scheduled.task
            
            # Skip if not pending
            if task.status != "pending":
                continue
            
            # Skip if already in progress or completed/failed
            if task.id in self.in_progress:
                continue
            if task.id in self.completed:
                continue
            if task.id in self.failed:
                continue
            
            # Check if all dependencies are completed
            deps_met = all(dep_id in self.completed for dep_id in task.deps)
            if deps_met:
                ready_tasks.append(task)
        
        # Sort by priority (descending) and level (ascending)
        ready_tasks.sort(key=lambda t: (-t.priority, self.scheduled_tasks[t.id].level))
        
        return ready_tasks[:batch_size]
    
    def mark_in_progress(self, task_id: str) -> None:
        """Mark task as in progress."""
        self.in_progress.add(task_id)
        task = self.task_graph.get_task(task_id)
        if task:
            task.status = "in_progress"
    
    def mark_completed(self, task_id: str) -> None:
        """Mark task as completed."""
        if task_id in self.in_progress:
            self.in_progress.remove(task_id)
        self.completed.add(task_id)
        task = self.task_graph.get_task(task_id)
        if task:
            task.status = "completed"
        logger.info(f"Task {task_id} completed")
    
    def mark_failed(self, task_id: str) -> None:
        """Mark task as failed."""
        if task_id in self.in_progress:
            self.in_progress.remove(task_id)
        self.failed.add(task_id)
        task = self.task_graph.get_task(task_id)
        if task:
            task.status = "failed"
        logger.warning(f"Task {task_id} failed")
    
    def get_stats(self) -> Dict[str, int]:
        """Get scheduler statistics."""
        total = len(self.task_graph.tasks)
        return {
            "total": total,
            "completed": len(self.completed),
            "in_progress": len(self.in_progress),
            "failed": len(self.failed),
            "pending": total - len(self.completed) - len(self.in_progress) - len(self.failed),
        }
    
    def has_remaining_tasks(self) -> bool:
        """Check if there are tasks remaining to execute."""
        stats = self.get_stats()
        return stats["pending"] > 0 or stats["in_progress"] > 0
    
    def get_failed_tasks(self) -> List[Task]:
        """Get list of failed tasks."""
        return [
            self.task_graph.get_task(task_id)
            for task_id in self.failed
            if self.task_graph.get_task(task_id)
        ]
    
    def reset_failed_tasks(self) -> None:
        """Reset failed tasks to pending status for retry."""
        for task_id in self.failed:
            task = self.task_graph.get_task(task_id)
            if task:
                task.status = "pending"
        self.failed.clear()
        logger.info("Reset all failed tasks to pending")
