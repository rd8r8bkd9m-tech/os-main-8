"""SQLite state management for Swarm-1000."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .logger import logger


SCHEMA_VERSION = 1

MIGRATIONS = [
    # Migration 0 -> 1: Initial schema
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        area TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        priority INTEGER DEFAULT 5,
        status TEXT DEFAULT 'pending',
        assigned_to TEXT,
        inputs TEXT,
        expected_outputs TEXT,
        tests TEXT,
        definition_of_done TEXT,
        risk TEXT,
        dependencies TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal TEXT,
        status TEXT DEFAULT 'running',
        concurrency INTEGER DEFAULT 20,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        total_tasks INTEGER DEFAULT 0,
        completed_tasks INTEGER DEFAULT 0,
        failed_tasks INTEGER DEFAULT 0
    );
    
    CREATE TABLE IF NOT EXISTS commits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        run_id INTEGER NOT NULL,
        commit_sha TEXT,
        worker_id TEXT,
        branch TEXT,
        worktree_path TEXT,
        committed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (run_id) REFERENCES runs(id)
    );
    
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        commit_id INTEGER,
        reviewer_id TEXT,
        status TEXT DEFAULT 'pending',
        comments TEXT,
        reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (commit_id) REFERENCES commits(id)
    );
    
    CREATE TABLE IF NOT EXISTS failures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        run_id INTEGER NOT NULL,
        error_type TEXT,
        error_message TEXT,
        stack_trace TEXT,
        retry_count INTEGER DEFAULT 0,
        failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (run_id) REFERENCES runs(id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
    CREATE INDEX IF NOT EXISTS idx_tasks_area ON tasks(area);
    CREATE INDEX IF NOT EXISTS idx_commits_task ON commits(task_id);
    CREATE INDEX IF NOT EXISTS idx_reviews_task ON reviews(task_id);
    CREATE INDEX IF NOT EXISTS idx_failures_task ON failures(task_id);
    """,
]


@dataclass
class TaskRecord:
    """Task record from database."""
    id: str
    area: str
    title: str
    description: Optional[str] = None
    priority: int = 5
    status: str = "pending"
    assigned_to: Optional[str] = None
    inputs: Optional[str] = None
    expected_outputs: Optional[str] = None
    tests: Optional[str] = None
    definition_of_done: Optional[str] = None
    risk: Optional[str] = None
    dependencies: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StateManager:
    """Manages SQLite database for swarm state."""
    
    def __init__(self, db_path: Path):
        """
        Initialize state manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
    
    def connect(self) -> None:
        """Connect to database and run migrations."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._migrate()
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _migrate(self) -> None:
        """Run database migrations."""
        cursor = self.conn.cursor()
        
        # Check current version
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        if not cursor.fetchone():
            current_version = 0
        else:
            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            current_version = result[0] if result[0] else 0
        
        # Apply migrations
        for version, migration in enumerate(MIGRATIONS, start=1):
            if version > current_version:
                logger.info(f"Applying migration {version}")
                cursor.executescript(migration)
                cursor.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (version,)
                )
                self.conn.commit()
    
    def create_run(self, goal: str, concurrency: int, total_tasks: int) -> int:
        """Create a new run record."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO runs (goal, concurrency, total_tasks)
            VALUES (?, ?, ?)
            """,
            (goal, concurrency, total_tasks)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_run_status(self, run_id: int, status: str,
                         completed_tasks: Optional[int] = None,
                         failed_tasks: Optional[int] = None) -> None:
        """Update run status."""
        cursor = self.conn.cursor()
        if status == "completed":
            cursor.execute(
                """
                UPDATE runs
                SET status = ?, completed_at = CURRENT_TIMESTAMP,
                    completed_tasks = COALESCE(?, completed_tasks),
                    failed_tasks = COALESCE(?, failed_tasks)
                WHERE id = ?
                """,
                (status, completed_tasks, failed_tasks, run_id)
            )
        else:
            cursor.execute(
                """
                UPDATE runs
                SET status = ?,
                    completed_tasks = COALESCE(?, completed_tasks),
                    failed_tasks = COALESCE(?, failed_tasks)
                WHERE id = ?
                """,
                (status, completed_tasks, failed_tasks, run_id)
            )
        self.conn.commit()
    
    def insert_task(self, task: TaskRecord) -> None:
        """Insert a task into the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (
                id, area, title, description, priority, status,
                inputs, expected_outputs, tests, definition_of_done,
                risk, dependencies
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.id, task.area, task.title, task.description,
                task.priority, task.status, task.inputs,
                task.expected_outputs, task.tests,
                task.definition_of_done, task.risk, task.dependencies
            )
        )
        self.conn.commit()
    
    def update_task_status(self, task_id: str, status: str,
                          assigned_to: Optional[str] = None) -> None:
        """Update task status."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE tasks
            SET status = ?, assigned_to = COALESCE(?, assigned_to),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, assigned_to, task_id)
        )
        self.conn.commit()
    
    def get_tasks_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all tasks with a specific status."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status = ?", (status,))
        return [dict(row) for row in cursor.fetchall()]
    
    def record_failure(self, task_id: str, run_id: int,
                      error_type: str, error_message: str,
                      stack_trace: Optional[str] = None) -> None:
        """Record a task failure."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO failures (
                task_id, run_id, error_type, error_message, stack_trace
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, run_id, error_type, error_message, stack_trace)
        )
        self.conn.commit()
    
    def get_failed_tasks(self, run_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get failed tasks."""
        cursor = self.conn.cursor()
        if run_id:
            cursor.execute(
                """
                SELECT DISTINCT t.* FROM tasks t
                JOIN failures f ON t.id = f.task_id
                WHERE f.run_id = ?
                """,
                (run_id,)
            )
        else:
            cursor.execute(
                """
                SELECT DISTINCT t.* FROM tasks t
                JOIN failures f ON t.id = f.task_id
                """
            )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_run_stats(self, run_id: int) -> Dict[str, Any]:
        """Get statistics for a run."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        run = cursor.fetchone()
        if not run:
            return {}
        
        stats = dict(run)
        
        # Get task counts by status
        cursor.execute(
            """
            SELECT status, COUNT(*) as count
            FROM tasks
            GROUP BY status
            """
        )
        stats['status_counts'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        return stats
