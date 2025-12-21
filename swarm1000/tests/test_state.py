"""Tests for state management."""

import pytest
import tempfile
from pathlib import Path

from swarm1000.core.state import StateManager, TaskRecord, SCHEMA_VERSION


def test_state_manager_connect():
    """Test connecting to state database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        state = StateManager(db_path)
        
        assert not state.conn
        state.connect()
        assert state.conn is not None
        
        state.close()
        assert state.conn is None


def test_state_manager_migrations():
    """Test that migrations are applied."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        state = StateManager(db_path)
        state.connect()
        
        # Check schema version table exists
        cursor = state.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        assert cursor.fetchone()
        
        # Check current version
        cursor.execute("SELECT MAX(version) FROM schema_version")
        version = cursor.fetchone()[0]
        assert version == SCHEMA_VERSION
        
        state.close()


def test_state_manager_tables_created():
    """Test that all required tables are created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        state = StateManager(db_path)
        state.connect()
        
        cursor = state.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ["tasks", "runs", "commits", "reviews", "failures", "schema_version"]
        for table in required_tables:
            assert table in tables
        
        state.close()


def test_create_run():
    """Test creating a run record."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        state = StateManager(db_path)
        state.connect()
        
        run_id = state.create_run(
            goal="Test goal",
            concurrency=20,
            total_tasks=100
        )
        
        assert run_id > 0
        
        # Verify run was created
        cursor = state.conn.cursor()
        cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        run = cursor.fetchone()
        
        assert run
        assert run["goal"] == "Test goal"
        assert run["concurrency"] == 20
        assert run["total_tasks"] == 100
        assert run["status"] == "running"
        
        state.close()


def test_insert_task():
    """Test inserting a task."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        state = StateManager(db_path)
        state.connect()
        
        task = TaskRecord(
            id="task-0001",
            area="backend",
            title="Test task",
            description="Test description",
            priority=5,
            status="pending"
        )
        
        state.insert_task(task)
        
        # Verify task was inserted
        cursor = state.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task.id,))
        row = cursor.fetchone()
        
        assert row
        assert row["id"] == "task-0001"
        assert row["area"] == "backend"
        assert row["title"] == "Test task"
        
        state.close()


def test_update_task_status():
    """Test updating task status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        state = StateManager(db_path)
        state.connect()
        
        task = TaskRecord(
            id="task-0001",
            area="backend",
            title="Test task",
            status="pending"
        )
        state.insert_task(task)
        
        state.update_task_status("task-0001", "in_progress", assigned_to="agent-0042")
        
        # Verify update
        cursor = state.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", ("task-0001",))
        row = cursor.fetchone()
        
        assert row["status"] == "in_progress"
        assert row["assigned_to"] == "agent-0042"
        
        state.close()


def test_record_failure():
    """Test recording a failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        state = StateManager(db_path)
        state.connect()
        
        run_id = state.create_run("Test", 10, 50)
        
        state.record_failure(
            task_id="task-0001",
            run_id=run_id,
            error_type="quality_gate",
            error_message="Tests failed"
        )
        
        # Verify failure was recorded
        cursor = state.conn.cursor()
        cursor.execute("SELECT * FROM failures WHERE task_id = ?", ("task-0001",))
        row = cursor.fetchone()
        
        assert row
        assert row["error_type"] == "quality_gate"
        assert row["error_message"] == "Tests failed"
        
        state.close()


def test_get_run_stats():
    """Test getting run statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        state = StateManager(db_path)
        state.connect()
        
        run_id = state.create_run("Test", 20, 100)
        
        # Insert some tasks
        for i in range(10):
            task = TaskRecord(
                id=f"task-{i:04d}",
                area="backend",
                title=f"Task {i}",
                status="pending"
            )
            state.insert_task(task)
        
        stats = state.get_run_stats(run_id)
        
        assert stats["id"] == run_id
        assert stats["goal"] == "Test"
        assert stats["total_tasks"] == 100
        assert "status_counts" in stats
        
        state.close()


def test_get_failed_tasks():
    """Test getting failed tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        state = StateManager(db_path)
        state.connect()
        
        run_id = state.create_run("Test", 20, 10)
        
        # Insert tasks and mark some as failed
        for i in range(5):
            task = TaskRecord(
                id=f"task-{i:04d}",
                area="backend",
                title=f"Task {i}",
                status="pending"
            )
            state.insert_task(task)
            
            if i < 2:
                state.record_failure(f"task-{i:04d}", run_id, "error", "Failed")
        
        failed_tasks = state.get_failed_tasks(run_id)
        assert len(failed_tasks) == 2
        
        state.close()
