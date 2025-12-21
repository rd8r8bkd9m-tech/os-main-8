# Kolibri Swarm-1000 Orchestrator

## System Architecture

The Kolibri Swarm-1000 Orchestrator is a Python-based system that manages 1000 logical AI agents to parallelize development work across a repository.

### Key Concepts

#### Logical vs. Physical Agents

**Important**: The system manages 1000 **logical agents**. These are persona-based roles with different skills and responsibilities, but execution is constrained by physical resources.

- **Logical agents**: 1000 agents with unique IDs, roles, skills, and constraints
- **Physical workers**: Configurable pool of concurrent executors (default: 20)
- **Mapping**: Tasks are assigned to logical agents, but executed by worker pool

This design provides:
- Rich task assignment based on agent specialization
- Realistic attribution (commits by specific agent personas)
- Resource-controlled execution (no system overload)

#### Architecture Layers

```
┌─────────────────────────────────────────┐
│         CLI Interface (swarm.py)        │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│          Core Components                │
│  ┌────────────┐  ┌──────────────┐      │
│  │  Planner   │  │  Scheduler   │      │
│  └────────────┘  └──────────────┘      │
│  ┌────────────┐  ┌──────────────┐      │
│  │  Personas  │  │  Task Graph  │      │
│  └────────────┘  └──────────────┘      │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│        Execution Components             │
│  ┌────────────┐  ┌──────────────┐      │
│  │  Git Ops   │  │  Codex MCP   │      │
│  └────────────┘  └──────────────┘      │
│  ┌────────────┐  ┌──────────────┐      │
│  │Quality Gate│  │  State DB    │      │
│  └────────────┘  └──────────────┘      │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│          Worker Pool                    │
│  [Worker 1] [Worker 2] ... [Worker N]  │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│          Git Worktrees                  │
│  worktree-01  worktree-02  ...  worktree-N │
└─────────────────────────────────────────┘
```

### Components

#### 1. Planner

Generates task graphs based on:
- Inventory of discovered projects
- High-level goal
- Available logical agents (1000)

Outputs:
- Task graph with dependencies
- Epic groupings
- Task metadata (priority, risk, estimated time)

#### 2. Personas

Manages 1000 logical agent personas with distribution:
- 1 PM-Chief
- 3 PMs
- 10 Tech Leads
- 250 Backend Engineers
- 250 Frontend Engineers
- 150 Rust/Protocol Engineers
- 100 DevOps/SRE
- 120 QA/Automation
- 80 Security/Performance
- 36 Design/UX/Copywriting

Each persona has:
- Unique ID
- Role and seniority level
- Technology stack
- Coding style preferences
- Constraints and guidelines
- Review skill level (1-10)

#### 3. Scheduler

Manages task execution:
- Computes dependency levels (topological sort)
- Provides batches of ready tasks
- Tracks completed/failed/in-progress tasks
- Ensures dependencies are met before execution

#### 4. Git Operations

Manages git worktrees:
- Creates isolated development environments
- One worktree per worker (reused across tasks)
- Commits changes with persona attribution
- Manages branches (swarm/worker-XX)

#### 5. Codex MCP Integration

Integrates with Codex MCP for AI-powered changes:
- Sends natural language instructions
- Receives code changes
- Validates changes
- **Mock mode**: Available for demo without actual Codex

#### 6. Quality Gate

Enforces code quality:
- **Strict mode**: All checks must pass
- **Permissive mode**: Warnings allowed
- **Skip mode**: No checks (demo/testing)

Checks by language:
- Python: ruff, pytest
- JavaScript/TypeScript: eslint, tsc
- Rust: cargo check, cargo clippy
- C/C++: cmake config, make syntax

#### 7. State Database

SQLite database tracking:
- Tasks and their status
- Run metadata
- Commits and reviews
- Failures for retry

Schema includes:
- `tasks`: All tasks with metadata
- `runs`: Execution runs
- `commits`: Git commits per task
- `reviews`: Code review records
- `failures`: Failed task tracking

### Workflow

```
1. INVENTORY
   ↓
   Scan directories → Detect projects → Extract metadata
   ↓
   inventory.json

2. PLAN
   ↓
   Generate personas → Build task graph → Validate dependencies
   ↓
   personas_1000.jsonl + task_graph.json

3. RUN
   ↓
   Initialize state DB → Create worktrees → Start worker pool
   ↓
   For each task:
     - Scheduler provides ready task
     - Assign to worker
     - Worker creates instruction
     - Codex MCP applies change
     - Quality gate validates
     - Git commits change
     - Mark task complete
   ↓
   state.sqlite (updated)

4. MONITOR
   ↓
   Query state DB → Generate reports → Export status
```

### Safety Mechanisms

1. **Workspace Isolation**
   - Each worker operates in isolated worktree
   - No cross-worker interference
   - All changes confined to repository

2. **No External Modifications**
   - Will not modify files outside repository
   - Dry-run mode for dangerous operations
   - Explicit approval required for destructive changes

3. **Quality Gates**
   - Automated linting and testing
   - Prevents broken code from being committed
   - Configurable strictness

4. **State Persistence**
   - All progress saved to SQLite
   - Can resume after interruption
   - Failed tasks can be retried

5. **Resource Limits**
   - Concurrency control prevents overload
   - Timeout protection on external commands
   - Maximum file size limits

### Performance Characteristics

- **Concurrency**: 20 workers default (configurable 1-100)
- **Task throughput**: ~5-10 tasks/minute (depends on complexity)
- **Memory usage**: ~500MB + (50MB × workers)
- **Disk usage**: ~1GB per 100 tasks (worktrees + state)

### Energy Efficiency

Following Kolibri AI principles:
- Efficient worker pool (no idle processes)
- Reuses worktrees (avoids repeated cloning)
- Optimizes file I/O (streaming, caching)
- Quality gates timeout to prevent runaway processes

### Extensibility

The system is designed for extensibility:
- **Custom personas**: Modify role distribution
- **Custom planners**: Different task generation strategies
- **Custom quality gates**: Add language-specific checks
- **Custom MCP integrations**: Replace Codex with other AI systems

### Limitations

Current limitations:
1. No distributed execution (single machine only)
2. No real-time collaboration between agents
3. Mock Codex MCP by default (requires setup for real usage)
4. Limited to text-based code changes
5. No visual/UI design capabilities

### Future Enhancements

Planned improvements:
- Distributed worker pools (multi-machine)
- Real-time agent collaboration
- Visual diff review interface
- Integration with CI/CD pipelines
- Advanced conflict resolution
- Machine learning for task estimation
