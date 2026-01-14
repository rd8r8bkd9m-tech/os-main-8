"""Task planning and graph generation."""

import random

from .inventory import ProjectInventoryItem
from .logger import logger
from .tasks import Task, TaskGraph

AREAS = [
    "platform",
    "backend",
    "frontend",
    "rust",
    "protocol",
    "devops",
    "docs",
    "design",
    "qa",
    "security",
]


class TaskPlanner:
    """Generates task graphs based on goals and inventory."""

    def __init__(self, goal: str, budget_agents: int = 1000):
        """
        Initialize task planner.

        Args:
            goal: High-level goal for the swarm
            budget_agents: Maximum number of agents (affects task granularity)
        """
        self.goal = goal
        self.budget_agents = budget_agents

    def generate_task_graph(
        self,
        inventory: list[ProjectInventoryItem],
        task_count: int = 1000
    ) -> TaskGraph:
        """
        Generate a task graph based on inventory and goal.

        Args:
            inventory: List of discovered projects
            task_count: Target number of tasks to generate

        Returns:
            TaskGraph with tasks and epics
        """
        logger.info(f"Generating task graph for goal: {self.goal}")
        logger.info(f"Target task count: {task_count}")

        tasks = []
        epics = {}

        # Define epics
        epic_names = [
            "Platform Foundation",
            "Backend Services",
            "Frontend Applications",
            "Rust/WASM Components",
            "Protocol Implementation",
            "DevOps & Infrastructure",
            "Documentation",
            "Design System",
            "Quality Assurance",
            "Security Hardening",
        ]

        # Distribute tasks across epics
        tasks_per_epic = task_count // len(epic_names)

        task_id_counter = 1

        for epic_idx, epic_name in enumerate(epic_names):
            epic_task_ids = []
            area = AREAS[epic_idx % len(AREAS)]

            # Generate tasks for this epic
            for i in range(tasks_per_epic):
                task_id = f"task-{task_id_counter:04d}"
                task_id_counter += 1

                # Create dependencies (some tasks depend on earlier tasks)
                deps = []
                if i > 0 and epic_task_ids and random.random() < 0.3:
                    # Depend on 1-2 previous tasks in this epic
                    num_deps = min(random.randint(1, 2), len(epic_task_ids))
                    deps = random.sample(epic_task_ids, num_deps)

                # Generate task details
                task = self._generate_task(
                    task_id=task_id,
                    area=area,
                    epic_name=epic_name,
                    task_index=i,
                    deps=deps,
                    inventory=inventory
                )

                tasks.append(task)
                epic_task_ids.append(task_id)

            epics[epic_name] = epic_task_ids

        # Add inter-epic dependencies
        self._add_cross_epic_dependencies(tasks, epics)

        task_graph = TaskGraph(tasks=tasks, epics=epics)

        # Validate
        errors = task_graph.validate_dependencies()
        if errors:
            logger.warning(f"Task graph has {len(errors)} validation errors")
            for error in errors[:5]:
                logger.warning(f"  {error}")

        logger.info(f"Generated task graph with {len(tasks)} tasks and {len(epics)} epics")
        return task_graph

    def _generate_task(
        self,
        task_id: str,
        area: str,
        epic_name: str,
        task_index: int,
        deps: list[str],
        inventory: list[ProjectInventoryItem]
    ) -> Task:
        """Generate a single task."""

        # Task templates based on area
        templates = {
            "platform": [
                "Implement core platform service",
                "Add platform monitoring",
                "Optimize platform performance",
                "Refactor platform module",
            ],
            "backend": [
                "Implement REST API endpoint",
                "Add database migration",
                "Optimize database query",
                "Add caching layer",
                "Implement background job",
            ],
            "frontend": [
                "Implement UI component",
                "Add page route",
                "Optimize bundle size",
                "Add responsive design",
                "Implement state management",
            ],
            "rust": [
                "Implement Rust module",
                "Add WASM bindings",
                "Optimize memory usage",
                "Add FFI interface",
            ],
            "protocol": [
                "Implement protocol handler",
                "Add protocol tests",
                "Document protocol spec",
                "Optimize protocol performance",
            ],
            "devops": [
                "Add CI/CD pipeline",
                "Configure deployment",
                "Add monitoring dashboard",
                "Implement auto-scaling",
            ],
            "docs": [
                "Write API documentation",
                "Add architecture diagram",
                "Create tutorial",
                "Update runbook",
            ],
            "design": [
                "Design UI component",
                "Create design system",
                "Add accessibility features",
                "Optimize UX flow",
            ],
            "qa": [
                "Add unit tests",
                "Implement integration test",
                "Add performance test",
                "Create test fixtures",
            ],
            "security": [
                "Perform security audit",
                "Fix vulnerability",
                "Add authentication",
                "Implement rate limiting",
            ],
        }

        template = random.choice(templates.get(area, ["Complete task"]))
        title = f"{template} #{task_index + 1}"

        description = f"""
Task in {epic_name} epic.
Area: {area}
Goal alignment: {self.goal}

This task contributes to the overall Kolibri AI platform consolidation.
        """.strip()

        # Generate inputs/outputs based on area
        inputs = [
            f"Source code in {area} area",
            "Project requirements",
            "Design specifications",
        ]

        expected_outputs = [
            f"Implemented {template.lower()}",
            "Updated tests",
            "Documentation",
        ]

        tests = [
            "Unit tests pass",
            "Integration tests pass",
            "No linting errors",
        ]

        definition_of_done = [
            "Code implemented and tested",
            "Tests passing",
            "Documentation updated",
            "Code reviewed and approved",
        ]

        # Risk assessment
        risk_level = random.choice(["low", "low", "medium", "medium", "high"])

        # Priority (1-10)
        priority = random.randint(3, 9)

        # Estimated time (15-60 minutes)
        estimated_minutes = random.choice([15, 30, 45, 60])

        return Task(
            id=task_id,
            area=area,
            title=title,
            description=description,
            inputs=inputs,
            expected_outputs=expected_outputs,
            tests=tests,
            definition_of_done=definition_of_done,
            risk=risk_level,
            deps=deps,
            priority=priority,
            estimated_minutes=estimated_minutes,
        )

    def _add_cross_epic_dependencies(
        self,
        tasks: list[Task],
        epics: dict[str, list[str]]
    ) -> None:
        """Add dependencies between epics."""
        # Platform should be done first
        platform_tasks = epics.get("Platform Foundation", [])
        if not platform_tasks:
            return

        # Some backend tasks depend on platform
        backend_tasks = epics.get("Backend Services", [])
        if backend_tasks:
            for task_id in random.sample(backend_tasks, min(3, len(backend_tasks))):
                task = next(t for t in tasks if t.id == task_id)
                if platform_tasks:
                    task.deps.append(random.choice(platform_tasks[:5]))

        # Frontend depends on backend
        frontend_tasks = epics.get("Frontend Applications", [])
        if frontend_tasks and backend_tasks:
            for task_id in random.sample(frontend_tasks, min(3, len(frontend_tasks))):
                task = next(t for t in tasks if t.id == task_id)
                if backend_tasks:
                    task.deps.append(random.choice(backend_tasks[:10]))


def create_demo_task_graph(task_count: int = 50) -> TaskGraph:
    """Create a demo task graph for testing."""
    planner = TaskPlanner(
        goal="Demo: Build unified Kolibri platform",
        budget_agents=task_count
    )
    return planner.generate_task_graph(inventory=[], task_count=task_count)
