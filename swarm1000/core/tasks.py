"""Task data structures and utilities."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .logger import logger


@dataclass
class Task:
    """Represents a single task in the swarm."""
    id: str
    area: str
    title: str
    description: str
    inputs: list[str]
    expected_outputs: list[str]
    tests: list[str]
    definition_of_done: list[str]
    risk: str  # low, medium, high
    deps: list[str]  # task IDs this depends on
    priority: int  # 1-10, higher is more important
    estimated_minutes: int = 30
    status: str = "pending"
    assigned_to: str | None = None


@dataclass
class TaskGraph:
    """Collection of tasks with dependencies."""
    tasks: list[Task]
    epics: dict[str, list[str]]  # epic_name -> [task_ids]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "tasks": [asdict(task) for task in self.tasks],
            "epics": self.epics,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'TaskGraph':
        """Create TaskGraph from dictionary."""
        tasks = [Task(**task_data) for task_data in data.get("tasks", [])]
        epics = data.get("epics", {})
        return cls(tasks=tasks, epics=epics)

    def save(self, output_path: Path) -> None:
        """Save task graph to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved task graph with {len(self.tasks)} tasks to {output_path}")

    @classmethod
    def load(cls, input_path: Path) -> 'TaskGraph':
        """Load task graph from JSON file."""
        with open(input_path) as f:
            data = json.load(f)
        logger.info(f"Loaded task graph from {input_path}")
        return cls.from_dict(data)

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_tasks_by_area(self, area: str) -> list[Task]:
        """Get all tasks in a specific area."""
        return [task for task in self.tasks if task.area == area]

    def get_ready_tasks(self, completed_task_ids: set) -> list[Task]:
        """
        Get tasks that are ready to execute (all dependencies completed).
        
        Args:
            completed_task_ids: Set of task IDs that are completed
            
        Returns:
            List of tasks ready to execute
        """
        ready = []
        for task in self.tasks:
            if task.status != "pending":
                continue

            # Check if all dependencies are completed
            deps_met = all(dep_id in completed_task_ids for dep_id in task.deps)
            if deps_met:
                ready.append(task)

        return ready

    def validate_dependencies(self) -> list[str]:
        """
        Validate that all task dependencies exist and there are no cycles.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        task_ids = {task.id for task in self.tasks}

        # Check that all dependencies exist
        for task in self.tasks:
            for dep_id in task.deps:
                if dep_id not in task_ids:
                    errors.append(
                        f"Task {task.id} depends on non-existent task {dep_id}"
                    )

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)

            task = self.get_task(task_id)
            if not task:
                return False

            for dep_id in task.deps:
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True

            rec_stack.remove(task_id)
            return False

        for task in self.tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    errors.append(f"Circular dependency detected involving task {task.id}")

        return errors
