# Kolibri Swarm-1000 Orchestrator

A Python-based orchestration system that manages 1000 logical agents to parallelize work across repositories using git worktrees and worker pools.

## Overview

The Swarm-1000 Orchestrator enables massive parallel development by:
- Managing 1000 **logical agents** with different roles, skills, and specializations
- Executing tasks in parallel using a configurable worker pool (default: 20 concurrent workers)
- Using git worktrees for isolated development environments
- Integrating with Codex MCP for AI-powered code changes
- Enforcing quality gates and safety protocols

**Important**: The 1000 agents are a **logical model**. Actual execution is limited by the `--concurrency` parameter to prevent system overload.

## Installation

From the repository root:

```bash
# The package is included in the repository, no installation needed
# Run commands using:
python -m swarm1000.swarm <command>
```

## Quick Start

### 1. Inventory

Scan directories to discover projects:

```bash
python -m swarm1000.swarm inventory \
  --roots /path/to/projects /path/to/other/projects \
  --max-depth 6
```

This creates `swarm1000/data/inventory.json` with project metadata.

### 2. Plan

Generate a task graph and personas:

```bash
python -m swarm1000.swarm plan \
  --goal "Build unified Kolibri platform" \
  --budget-agents 1000
```

This creates:
- `swarm1000/data/personas_1000.jsonl` - 1000 agent personas
- `swarm1000/data/task_graph.json` - Task dependency graph

### 3. Run

Execute tasks with parallel workers:

```bash
python -m swarm1000.swarm run \
  --concurrency 20 \
  --mode worktree \
  --quality-gate strict
```

### 4. Monitor & Manage

Check status:
```bash
python -m swarm1000.swarm status
```

Export results:
```bash
python -m swarm1000.swarm export --output status.json
```

Rerun failed tasks:
```bash
python -m swarm1000.swarm rerun-failed
```

## Commands

### `inventory`
Scans directories recursively to build an inventory of projects with metadata:
- Programming languages detected
- Build systems (npm, cargo, cmake, etc.)
- Project size and file count
- Git activity (commits in last 30 days)
- README content

### `plan`
Generates execution plan:
- Creates 1000 personas with role distribution (PM, Backend, Frontend, Rust, DevOps, QA, Security, Design)
- Builds task dependency graph with epics and micro-tasks
- Each task includes: inputs, outputs, tests, definition of done, dependencies, priority

### `run`
Executes tasks in parallel:
- Respects task dependencies
- Uses worker pool for concurrency control
- Creates git worktrees per worker (optional)
- Applies changes via Codex MCP (with mock mode)
- Runs quality gate checks (lint/test/build)
- Commits changes with persona attribution

### `status`
Shows current execution status:
- Run statistics
- Task counts by status
- Progress summary

### `export`
Exports task status to JSON file for external analysis

### `rerun-failed`
Resets failed tasks to pending for retry

### `pause` / `resume`
Placeholders for execution control (use Ctrl+C and rerun)

## Architecture

```
swarm1000/
├── core/              # Core modules
│   ├── config.py      # Configuration management
│   ├── logger.py      # Logging infrastructure
│   ├── state.py       # SQLite state management
│   ├── personas.py    # Persona generation
│   ├── inventory.py   # Directory scanning
│   ├── tasks.py       # Task data structures
│   ├── planner.py     # Task graph generation
│   ├── scheduler.py   # Dependency-aware scheduling
│   ├── git_ops.py     # Git worktree operations
│   ├── codex_mcp.py   # Codex MCP integration
│   └── quality_gate.py # Quality checks
├── data/              # Generated data (not committed)
│   ├── inventory.json
│   ├── task_graph.json
│   ├── personas_1000.jsonl
│   └── state.sqlite   # SQLite database
├── templates/         # Task templates
├── scripts/           # Helper scripts
└── swarm.py          # CLI entry point
```

## Safety & Security

The orchestrator follows strict safety protocols:

1. **No destructive operations outside repository**
   - Will not delete/move files in external paths
   - All changes confined to repository/worktrees

2. **Dry-run for dangerous operations**
   - Mass rename/delete requires explicit approval
   - DRY RUN mode reports changes without applying

3. **Quality gates**
   - Lint, test, build checks before commit
   - Configurable strictness (strict/permissive/skip)

4. **No secrets in logs or commits**
   - `.env` files respected
   - Sensitive data never logged

5. **Workspace isolation**
   - Each worker operates in isolated worktree
   - No interference between workers

## Configuration

Default configuration (can be customized):

```python
- concurrency: 20 workers
- max_depth: 6 directories
- quality_gate: strict
- mode: worktree
- codex_mcp: mock (for demo)
```

## Requirements

- Python 3.10+
- Git (for worktree management)
- Optional: Codex MCP server (mock mode available)
- Optional: Language-specific tools (pytest, eslint, cargo, etc.) for quality gates

## Documentation

See `docs/` directory for detailed documentation:
- `SWARM1000.md` - System architecture
- `GOVERNANCE.md` - Development governance
- `RUNBOOK.md` - Operations guide
- `SAFETY.md` - Safety protocols
- `INVENTORY_SCHEMA.md` - Inventory format
- `TASK_GRAPH.md` - Task graph structure

## License

MIT License - See repository LICENSE file
