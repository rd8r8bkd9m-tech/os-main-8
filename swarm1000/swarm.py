#!/usr/bin/env python3
"""
Kolibri Swarm-1000 Orchestrator CLI

Main command-line interface for managing 1000 logical agents.
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .core.codex_mcp import CodexMCP
from .core.config import get_default_config
from .core.git_ops import GitOps
from .core.inventory import InventoryScanner, load_inventory, save_inventory
from .core.logger import logger
from .core.personas import generate_personas, load_personas_jsonl, save_personas_jsonl
from .core.planner import TaskPlanner
from .core.quality_gate import QualityGate, QualityGateMode
from .core.scheduler import TaskScheduler
from .core.state import StateManager, TaskRecord
from .core.tasks import TaskGraph


def cmd_inventory(args):
    """Run inventory command."""
    logger.info("=== Inventory Scan ===")

    config = get_default_config()
    scanner = InventoryScanner(
        max_depth=args.max_depth,
        max_file_size_mb=args.max_file_size,
    )

    items = scanner.scan_roots(args.roots)

    output_path = config.repo_root / "swarm1000" / "data" / "inventory.json"
    save_inventory(items, output_path)

    logger.info(f"Scanned {len(items)} projects")
    logger.info(f"Inventory saved to {output_path}")


def cmd_plan(args):
    """Run plan command."""
    logger.info("=== Task Planning ===")

    config = get_default_config()

    # Generate personas
    logger.info(f"Generating {args.budget_agents} personas...")
    personas = generate_personas(args.budget_agents)
    personas_path = config.repo_root / "swarm1000" / "data" / "personas_1000.jsonl"
    save_personas_jsonl(personas, personas_path)

    # Load inventory if it exists
    inventory_path = config.repo_root / "swarm1000" / "data" / "inventory.json"
    inventory = []
    if inventory_path.exists():
        inventory = load_inventory(inventory_path)
        logger.info(f"Loaded inventory with {len(inventory)} projects")
    else:
        logger.warning("No inventory found, generating plan without inventory")

    # Generate task graph
    planner = TaskPlanner(goal=args.goal, budget_agents=args.budget_agents)
    task_graph = planner.generate_task_graph(inventory, task_count=args.budget_agents)

    # Save task graph
    task_graph_path = config.repo_root / "swarm1000" / "data" / "task_graph.json"
    task_graph.save(task_graph_path)

    # Validate
    errors = task_graph.validate_dependencies()
    if errors:
        logger.warning(f"Task graph has {len(errors)} validation errors")
    else:
        logger.info("Task graph validation passed")

    logger.info(f"Generated {len(task_graph.tasks)} tasks")
    logger.info(f"Task graph saved to {task_graph_path}")


def cmd_run(args):
    """Run execution command."""
    logger.info("=== Swarm Execution ===")

    config = get_default_config()

    # Load task graph
    task_graph_path = config.repo_root / "swarm1000" / "data" / "task_graph.json"
    if not task_graph_path.exists():
        logger.error("Task graph not found. Run 'plan' command first.")
        sys.exit(1)

    task_graph = TaskGraph.load(task_graph_path)
    logger.info(f"Loaded {len(task_graph.tasks)} tasks")

    # Initialize state database
    state = StateManager(config.state_db_path)
    state.connect()

    # Create run record
    run_id = state.create_run(
        goal="Execute swarm tasks",
        concurrency=args.concurrency,
        total_tasks=len(task_graph.tasks)
    )
    logger.info(f"Created run #{run_id}")

    # Insert tasks into database
    for task in task_graph.tasks:
        task_record = TaskRecord(
            id=task.id,
            area=task.area,
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            inputs=json.dumps(task.inputs),
            expected_outputs=json.dumps(task.expected_outputs),
            tests=json.dumps(task.tests),
            definition_of_done=json.dumps(task.definition_of_done),
            risk=task.risk,
            dependencies=json.dumps(task.deps),
        )
        state.insert_task(task_record)

    # Initialize components
    scheduler = TaskScheduler(task_graph)
    git_ops = None
    codex_mcp = CodexMCP(mock_mode=True)
    quality_gate = QualityGate(mode=QualityGateMode[args.quality_gate.upper()])

    if args.mode == "worktree":
        git_ops = GitOps(config.repo_root, config.workspace_root)
        logger.info(f"Worktree mode enabled. Workspace: {config.workspace_root}")

    # Start Codex MCP
    codex_mcp.start_server()

    logger.info(f"Concurrency: {args.concurrency}")
    logger.info(f"Quality gate: {args.quality_gate}")
    logger.info(f"Mode: {args.mode}")
    logger.info("")
    logger.info("NOTE: 1000 agents is a LOGICAL model.")
    logger.info(f"Actual execution is limited to {args.concurrency} concurrent workers.")
    logger.info("")

    # Load personas
    personas_path = config.repo_root / "swarm1000" / "data" / "personas_1000.jsonl"
    personas = []
    if personas_path.exists():
        personas = load_personas_jsonl(personas_path)

    # Execute tasks
    completed_count = 0
    failed_count = 0

    try:
        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            while scheduler.has_remaining_tasks():
                # Get next batch
                batch = scheduler.get_next_batch(args.concurrency)

                if not batch:
                    logger.info("No tasks ready, waiting for dependencies...")
                    break

                logger.info(f"Executing batch of {len(batch)} tasks...")

                # Submit tasks
                futures = {}
                for task in batch:
                    scheduler.mark_in_progress(task.id)
                    state.update_task_status(task.id, "in_progress")

                    # Assign persona
                    persona = None
                    if personas and len(personas) > 0:
                        persona = personas[hash(task.id) % len(personas)]

                    future = executor.submit(
                        execute_task,
                        task, persona, config, git_ops, codex_mcp, quality_gate, args.mode
                    )
                    futures[future] = task

                # Wait for completion
                for future in as_completed(futures):
                    task = futures[future]
                    try:
                        result = future.result()
                        if result["success"]:
                            scheduler.mark_completed(task.id)
                            state.update_task_status(task.id, "completed")
                            completed_count += 1
                            logger.info(f"✓ {task.id}: {task.title}")
                        else:
                            scheduler.mark_failed(task.id)
                            state.update_task_status(task.id, "failed")
                            state.record_failure(
                                task.id, run_id,
                                error_type="execution",
                                error_message=result.get("error", "Unknown error")
                            )
                            failed_count += 1
                            logger.error(f"✗ {task.id}: {result.get('error')}")
                    except Exception as e:
                        scheduler.mark_failed(task.id)
                        state.update_task_status(task.id, "failed")
                        state.record_failure(
                            task.id, run_id,
                            error_type="exception",
                            error_message=str(e)
                        )
                        failed_count += 1
                        logger.error(f"✗ {task.id}: Exception: {e}")

                # Update run stats
                state.update_run_status(run_id, "running", completed_count, failed_count)

                stats = scheduler.get_stats()
                logger.info(f"Progress: {completed_count}/{stats['total']} completed, {failed_count} failed")

    finally:
        codex_mcp.stop_server()
        state.update_run_status(run_id, "completed", completed_count, failed_count)
        state.close()

    logger.info("=== Run Complete ===")
    logger.info(f"Completed: {completed_count}")
    logger.info(f"Failed: {failed_count}")


def execute_task(task, persona, config, git_ops, codex_mcp, quality_gate, mode):
    """Execute a single task."""
    result = {"success": False}

    try:
        # Determine working directory
        if mode == "worktree" and git_ops:
            worker_id = f"worker-{hash(task.id) % 100:02d}"
            workdir = git_ops.create_worktree(worker_id)
        else:
            workdir = config.repo_root

        # Apply change via Codex MCP
        instruction = f"""
Task: {task.title}
Area: {task.area}
Description: {task.description}

Expected outputs: {', '.join(task.expected_outputs)}
Tests: {', '.join(task.tests)}
Definition of Done: {', '.join(task.definition_of_done)}
        """

        change_result = codex_mcp.apply_change(
            workdir=workdir,
            instruction=instruction,
            files_hint=None
        )

        if not change_result.get("success"):
            result["error"] = change_result.get("error", "Failed to apply change")
            return result

        # Run quality gate
        qg_result = quality_gate.check(workdir, task.area)

        if not qg_result["passed"]:
            result["error"] = "Quality gate failed"
            result["quality_gate"] = qg_result
            return result

        # Commit changes if in worktree mode
        if mode == "worktree" and git_ops:
            author = f"{persona.role} <swarm@kolibri.ai>" if persona else None
            commit_sha = git_ops.commit_changes(
                workdir,
                message=f"{task.title}\n\n{task.description}",
                author=author
            )
            result["commit_sha"] = commit_sha

        result["success"] = True
        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def cmd_status(args):
    """Show status command."""
    config = get_default_config()

    state = StateManager(config.state_db_path)
    if not config.state_db_path.exists():
        logger.error("No run state found. Run 'run' command first.")
        sys.exit(1)

    state.connect()

    # Get latest run
    cursor = state.conn.cursor()
    cursor.execute("SELECT MAX(id) FROM runs")
    latest_run_id = cursor.fetchone()[0]

    if not latest_run_id:
        logger.info("No runs found")
        state.close()
        return

    stats = state.get_run_stats(latest_run_id)

    logger.info("=== Swarm Status ===")
    logger.info(f"Run ID: {latest_run_id}")
    logger.info(f"Status: {stats.get('status')}")
    logger.info(f"Goal: {stats.get('goal')}")
    logger.info(f"Concurrency: {stats.get('concurrency')}")
    logger.info(f"Started: {stats.get('started_at')}")
    logger.info("")
    logger.info(f"Total tasks: {stats.get('total_tasks')}")
    logger.info(f"Completed: {stats.get('completed_tasks')}")
    logger.info(f"Failed: {stats.get('failed_tasks')}")
    logger.info("")

    status_counts = stats.get('status_counts', {})
    for status, count in status_counts.items():
        logger.info(f"  {status}: {count}")

    state.close()


def cmd_export(args):
    """Export status to file."""
    config = get_default_config()

    state = StateManager(config.state_db_path)
    if not config.state_db_path.exists():
        logger.error("No run state found.")
        sys.exit(1)

    state.connect()

    # Export all tasks
    cursor = state.conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = [dict(row) for row in cursor.fetchall()]

    output = {
        "version": "1.0",
        "total_tasks": len(tasks),
        "tasks": tasks,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info(f"Exported {len(tasks)} tasks to {output_path}")
    state.close()


def cmd_rerun_failed(args):
    """Rerun failed tasks."""
    config = get_default_config()

    state = StateManager(config.state_db_path)
    if not config.state_db_path.exists():
        logger.error("No run state found.")
        sys.exit(1)

    state.connect()

    # Get failed tasks
    failed_tasks = state.get_failed_tasks()

    if not failed_tasks:
        logger.info("No failed tasks found")
        state.close()
        return

    logger.info(f"Found {len(failed_tasks)} failed tasks")

    # Reset to pending
    for task_data in failed_tasks:
        state.update_task_status(task_data['id'], 'pending')

    state.close()

    logger.info(f"Reset {len(failed_tasks)} tasks to pending")
    logger.info("Run 'run' command again to retry")


def cmd_pause(args):
    """Pause execution (placeholder)."""
    logger.warning("Pause command not yet implemented")
    logger.info("To stop execution, use Ctrl+C")


def cmd_resume(args):
    """Resume execution (placeholder)."""
    logger.warning("Resume command not yet implemented")
    logger.info("Simply run 'run' command again to continue")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Kolibri Swarm-1000 Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # inventory command
    inventory_parser = subparsers.add_parser(
        "inventory",
        help="Scan directories and build inventory"
    )
    inventory_parser.add_argument(
        "--roots",
        nargs="+",
        required=True,
        help="Root directories to scan"
    )
    inventory_parser.add_argument(
        "--max-depth",
        type=int,
        default=6,
        help="Maximum directory depth (default: 6)"
    )
    inventory_parser.add_argument(
        "--max-file-size",
        type=int,
        default=5,
        help="Maximum file size to read in MB (default: 5)"
    )

    # plan command
    plan_parser = subparsers.add_parser(
        "plan",
        help="Generate task plan and personas"
    )
    plan_parser.add_argument(
        "--goal",
        required=True,
        help="High-level goal for the swarm"
    )
    plan_parser.add_argument(
        "--budget-agents",
        type=int,
        default=1000,
        help="Number of logical agents (default: 1000)"
    )

    # run command
    run_parser = subparsers.add_parser(
        "run",
        help="Execute tasks with workers"
    )
    run_parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
        help="Number of concurrent workers (default: 20)"
    )
    run_parser.add_argument(
        "--mode",
        choices=["worktree", "single"],
        default="worktree",
        help="Execution mode (default: worktree)"
    )
    run_parser.add_argument(
        "--quality-gate",
        choices=["strict", "permissive", "skip"],
        default="strict",
        help="Quality gate mode (default: strict)"
    )

    # status command
    subparsers.add_parser(
        "status",
        help="Show current status"
    )

    # export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export status to file"
    )
    export_parser.add_argument(
        "--output",
        required=True,
        help="Output file path"
    )

    # rerun-failed command
    subparsers.add_parser(
        "rerun-failed",
        help="Rerun failed tasks"
    )

    # pause/resume commands
    subparsers.add_parser("pause", help="Pause execution")
    subparsers.add_parser("resume", help="Resume execution")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    command_map = {
        "inventory": cmd_inventory,
        "plan": cmd_plan,
        "run": cmd_run,
        "status": cmd_status,
        "export": cmd_export,
        "rerun-failed": cmd_rerun_failed,
        "pause": cmd_pause,
        "resume": cmd_resume,
    }

    command_map[args.command](args)


if __name__ == "__main__":
    main()
