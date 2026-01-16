"""Tests for task scheduler."""

from swarm1000.core.planner import create_demo_task_graph
from swarm1000.core.scheduler import TaskScheduler


def test_scheduler_initialization():
    """Test scheduler initialization."""
    task_graph = create_demo_task_graph(task_count=20)
    scheduler = TaskScheduler(task_graph)

    assert scheduler.task_graph == task_graph
    assert len(scheduler.completed) == 0
    assert len(scheduler.in_progress) == 0
    assert len(scheduler.failed) == 0


def test_scheduler_get_next_batch():
    """Test getting next batch of tasks."""
    task_graph = create_demo_task_graph(task_count=20)
    scheduler = TaskScheduler(task_graph)

    batch = scheduler.get_next_batch(batch_size=5)

    # Should get some tasks (those with no dependencies)
    assert len(batch) > 0
    assert len(batch) <= 5

    # All tasks should be pending
    for task in batch:
        assert task.status == "pending"


def test_scheduler_respects_dependencies():
    """Test that scheduler respects task dependencies."""
    task_graph = create_demo_task_graph(task_count=50)
    scheduler = TaskScheduler(task_graph)

    # Get first batch
    batch1 = scheduler.get_next_batch(batch_size=10)

    # All tasks in first batch should have no dependencies or met dependencies
    for task in batch1:
        for dep_id in task.deps:
            # If there are deps, they should be in completed set
            # (which is empty initially, so no deps for first batch)
            assert dep_id in scheduler.completed or len(task.deps) == 0


def test_scheduler_mark_completed():
    """Test marking tasks as completed."""
    task_graph = create_demo_task_graph(task_count=10)
    scheduler = TaskScheduler(task_graph)

    batch = scheduler.get_next_batch(batch_size=5)
    task = batch[0]

    scheduler.mark_in_progress(task.id)
    assert task.id in scheduler.in_progress

    scheduler.mark_completed(task.id)
    assert task.id in scheduler.completed
    assert task.id not in scheduler.in_progress


def test_scheduler_mark_failed():
    """Test marking tasks as failed."""
    task_graph = create_demo_task_graph(task_count=10)
    scheduler = TaskScheduler(task_graph)

    batch = scheduler.get_next_batch(batch_size=5)
    task = batch[0]

    scheduler.mark_in_progress(task.id)
    scheduler.mark_failed(task.id)

    assert task.id in scheduler.failed
    assert task.id not in scheduler.in_progress


def test_scheduler_stats():
    """Test scheduler statistics."""
    task_graph = create_demo_task_graph(task_count=20)
    scheduler = TaskScheduler(task_graph)

    stats = scheduler.get_stats()

    assert stats["total"] == 20
    assert stats["completed"] == 0
    assert stats["in_progress"] == 0
    assert stats["failed"] == 0
    assert stats["pending"] == 20


def test_scheduler_has_remaining_tasks():
    """Test checking for remaining tasks."""
    task_graph = create_demo_task_graph(task_count=10)
    scheduler = TaskScheduler(task_graph)

    assert scheduler.has_remaining_tasks()

    # Complete all tasks
    for task in task_graph.tasks:
        scheduler.mark_completed(task.id)

    assert not scheduler.has_remaining_tasks()


def test_scheduler_dependency_levels():
    """Test that scheduler computes dependency levels."""
    task_graph = create_demo_task_graph(task_count=50)
    scheduler = TaskScheduler(task_graph)

    # Check that levels are computed
    for _task_id, scheduled in scheduler.scheduled_tasks.items():
        assert isinstance(scheduled.level, int)
        assert scheduled.level >= 0


def test_scheduler_priority_ordering():
    """Test that higher priority tasks are scheduled first."""
    task_graph = create_demo_task_graph(task_count=20)
    scheduler = TaskScheduler(task_graph)

    # Get a batch
    batch = scheduler.get_next_batch(batch_size=10)

    # Within tasks with no dependencies, higher priority should come first
    if len(batch) > 1:
        priorities = [task.priority for task in batch]
        # Should be in descending order (higher first)
        assert priorities == sorted(priorities, reverse=True)


def test_scheduler_reset_failed():
    """Test resetting failed tasks."""
    task_graph = create_demo_task_graph(task_count=10)
    scheduler = TaskScheduler(task_graph)

    # Fail some tasks
    batch = scheduler.get_next_batch(batch_size=3)
    for task in batch:
        scheduler.mark_in_progress(task.id)
        scheduler.mark_failed(task.id)

    assert len(scheduler.failed) == 3

    # Reset
    scheduler.reset_failed_tasks()
    assert len(scheduler.failed) == 0

    # Tasks should be back to pending
    for task in batch:
        assert task.status == "pending"
