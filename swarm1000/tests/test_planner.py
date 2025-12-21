"""Tests for task planner."""

from swarm1000.core.planner import TaskPlanner, create_demo_task_graph
from swarm1000.core.inventory import ProjectInventoryItem


def test_create_demo_task_graph():
    """Test creating a demo task graph."""
    task_graph = create_demo_task_graph(task_count=50)
    
    assert len(task_graph.tasks) == 50
    assert len(task_graph.epics) > 0


def test_task_graph_has_valid_tasks():
    """Test that generated tasks have required fields."""
    task_graph = create_demo_task_graph(task_count=20)
    
    for task in task_graph.tasks:
        assert task.id
        assert task.area
        assert task.title
        assert task.description
        assert isinstance(task.inputs, list)
        assert isinstance(task.expected_outputs, list)
        assert isinstance(task.tests, list)
        assert isinstance(task.definition_of_done, list)
        assert task.risk in ["low", "medium", "high"]
        assert isinstance(task.deps, list)
        assert 1 <= task.priority <= 10
        assert task.estimated_minutes > 0


def test_task_graph_dependencies_exist():
    """Test that all task dependencies reference existing tasks."""
    task_graph = create_demo_task_graph(task_count=50)
    
    task_ids = {task.id for task in task_graph.tasks}
    
    for task in task_graph.tasks:
        for dep_id in task.deps:
            assert dep_id in task_ids, f"Task {task.id} depends on non-existent {dep_id}"


def test_task_graph_no_cycles():
    """Test that task graph has no circular dependencies."""
    task_graph = create_demo_task_graph(task_count=50)
    
    errors = task_graph.validate_dependencies()
    
    # Filter for cycle errors
    cycle_errors = [e for e in errors if "circular" in e.lower()]
    assert len(cycle_errors) == 0


def test_task_planner_with_inventory():
    """Test task planner with inventory."""
    inventory = [
        ProjectInventoryItem(
            path="/test/project1",
            name="project1",
            languages=["Python"],
            build_systems=["python-pip"],
            size_kb=1000,
            file_count=50,
            git_active=True,
            git_commits_30d=10,
            readme_content="Test project",
            metadata={"has_tests": True, "has_docs": False}
        )
    ]
    
    planner = TaskPlanner(
        goal="Test goal",
        budget_agents=100
    )
    
    task_graph = planner.generate_task_graph(inventory, task_count=20)
    assert len(task_graph.tasks) == 20


def test_task_graph_areas_distribution():
    """Test that tasks are distributed across different areas."""
    task_graph = create_demo_task_graph(task_count=100)
    
    areas = {task.area for task in task_graph.tasks}
    
    # Should have multiple areas
    assert len(areas) >= 5


def test_task_graph_epic_assignment():
    """Test that all tasks are assigned to epics."""
    task_graph = create_demo_task_graph(task_count=50)
    
    tasks_in_epics = set()
    for epic_tasks in task_graph.epics.values():
        tasks_in_epics.update(epic_tasks)
    
    task_ids = {task.id for task in task_graph.tasks}
    
    # All tasks should be in at least one epic
    assert tasks_in_epics == task_ids
