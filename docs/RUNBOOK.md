# Runbook: Kolibri Swarm-1000 Operations

## Overview

This runbook provides operational procedures for running the Kolibri Swarm-1000 Orchestrator.

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **Git**: 2.30 or higher
- **Disk Space**: 10GB+ recommended
- **Memory**: 4GB+ (8GB+ for high concurrency)
- **OS**: macOS, Linux (Windows via WSL)

### Optional Tools

- **ruff**: Python linting
- **pytest**: Python testing
- **npm**: JavaScript/TypeScript projects
- **cargo**: Rust projects
- **cmake**: C/C++ projects

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/rd8r8bkd9m-tech/os-main-8.git
cd os-main-8
```

### 2. Bootstrap

```bash
cd swarm1000
./scripts/bootstrap.sh
```

This checks:
- Python version
- Git installation
- Creates data directory
- Reports optional tools

### 3. Verify Installation

```bash
python -m swarm1000.swarm --help
```

Should display command help.

## Basic Operations

### Running a Complete Workflow

#### Step 1: Inventory

Scan your development directories:

```bash
python -m swarm1000.swarm inventory \
  --roots ~/Documents ~/Projects \
  --max-depth 6
```

**Output**: `swarm1000/data/inventory.json`

**Time**: 1-5 minutes depending on directory size

#### Step 2: Plan

Generate task plan:

```bash
python -m swarm1000.swarm plan \
  --goal "Build unified Kolibri platform" \
  --budget-agents 1000
```

**Outputs**:
- `swarm1000/data/personas_1000.jsonl`
- `swarm1000/data/task_graph.json`

**Time**: 10-30 seconds

Review the task graph before proceeding:

```bash
cat swarm1000/data/task_graph.json | jq '.tasks | length'
```

#### Step 3: Run

Execute tasks:

```bash
python -m swarm1000.swarm run \
  --concurrency 20 \
  --mode worktree \
  --quality-gate strict
```

**Concurrency**: Number of parallel workers (1-100, default 20)

**Mode**:
- `worktree`: Use git worktrees (recommended)
- `single`: Single workspace (for testing)

**Quality Gate**:
- `strict`: All checks must pass
- `permissive`: Warnings allowed
- `skip`: No checks (demo only)

**Time**: Varies by task count and complexity

Press `Ctrl+C` to stop (progress is saved).

#### Step 4: Monitor

Check status:

```bash
python -m swarm1000.swarm status
```

Export results:

```bash
python -m swarm1000.swarm export \
  --output results.json
```

## Advanced Operations

### Demo Mode

Run quick demo:

```bash
cd swarm1000
./scripts/swarm_demo.sh
```

This runs a complete workflow with:
- Current repository inventory
- 50 tasks
- 5 concurrent workers
- Single mode (no worktrees)
- Skip quality gate

### Custom Workflow

#### Inventory Specific Directories

```bash
python -m swarm1000.swarm inventory \
  --roots /path/to/project1 /path/to/project2 \
  --max-depth 4 \
  --max-file-size 10
```

#### Generate Smaller Task Set

```bash
python -m swarm1000.swarm plan \
  --goal "Quick prototype" \
  --budget-agents 100
```

#### Run with Custom Settings

```bash
python -m swarm1000.swarm run \
  --concurrency 5 \
  --mode single \
  --quality-gate permissive
```

### Retry Failed Tasks

After a run with failures:

```bash
python -m swarm1000.swarm rerun-failed
python -m swarm1000.swarm run --concurrency 10
```

### Manual Worktree Management

Create worktrees manually:

```bash
cd swarm1000
./scripts/make_worktrees.sh 20
```

List worktrees:

```bash
git worktree list
```

Remove worktree:

```bash
git worktree remove /path/to/worktree --force
```

## Troubleshooting

### Common Issues

#### Issue: "Task graph not found"

**Symptom**: Error when running `run` command

**Solution**: Run `plan` command first

```bash
python -m swarm1000.swarm plan --goal "..." --budget-agents 1000
```

#### Issue: "Permission denied" during inventory

**Symptom**: Warnings about inaccessible directories

**Solution**: Skip those directories or run with appropriate permissions

#### Issue: Quality gate failures

**Symptom**: All tasks failing with quality gate errors

**Solutions**:
1. Run with `--quality-gate permissive`
2. Install required tools (ruff, pytest, etc.)
3. Run with `--quality-gate skip` for testing

#### Issue: Out of disk space

**Symptom**: Worktree creation fails

**Solution**:
1. Reduce concurrency
2. Clean up old worktrees
3. Use `--mode single` instead

```bash
# Remove all worktrees
cd <repo>-swarm/workers
for d in worker-*; do
  git -C <repo> worktree remove "$PWD/$d" --force
done
```

#### Issue: Database locked

**Symptom**: SQLite errors during run

**Solution**: Stop all concurrent runs, wait for locks to clear

```bash
# Check for locks
lsof swarm1000/data/state.sqlite

# Remove database (loses progress!)
rm swarm1000/data/state.sqlite
```

### Performance Issues

#### Slow execution

**Causes**:
- Too many workers for system
- Large files being processed
- Network issues (git operations)

**Solutions**:
1. Reduce `--concurrency`
2. Increase file size limits
3. Use local git repos

#### High memory usage

**Causes**:
- Too many concurrent workers
- Large task graphs

**Solutions**:
1. Reduce `--concurrency`
2. Use smaller `--budget-agents`
3. Close other applications

## Monitoring

### Watch Real-time Progress

```bash
# In one terminal
python -m swarm1000.swarm run --concurrency 20

# In another terminal
watch -n 5 'python -m swarm1000.swarm status'
```

### Check Logs

Logs are written to stdout. Redirect to file:

```bash
python -m swarm1000.swarm run --concurrency 20 2>&1 | tee swarm_run.log
```

### Database Queries

Query state directly:

```bash
sqlite3 swarm1000/data/state.sqlite

# Example queries:
SELECT status, COUNT(*) FROM tasks GROUP BY status;
SELECT * FROM tasks WHERE status='failed';
SELECT * FROM runs ORDER BY id DESC LIMIT 1;
```

## Maintenance

### Cleanup

Remove generated data:

```bash
rm -rf swarm1000/data/*.json
rm -rf swarm1000/data/*.jsonl
rm -rf swarm1000/data/state.sqlite
```

Remove worktrees:

```bash
git worktree list | grep swarm/ | awk '{print $1}' | xargs -I {} git worktree remove {} --force
```

### Reset State

Start fresh:

```bash
# Remove all generated data
rm -rf swarm1000/data/*

# Remove all worktrees
git worktree list | grep swarm/ | awk '{print $1}' | xargs -I {} git worktree remove {} --force

# Run workflow from scratch
python -m swarm1000.swarm inventory --roots ~/Projects
python -m swarm1000.swarm plan --goal "..." --budget-agents 1000
python -m swarm1000.swarm run --concurrency 20
```

## Best Practices

1. **Start small**: Test with `--budget-agents 50` first
2. **Use appropriate concurrency**: Match to CPU cores (typically 1-2x cores)
3. **Monitor resources**: Watch CPU, memory, disk usage
4. **Regular status checks**: Monitor progress frequently
5. **Save results**: Export status regularly
6. **Clean up**: Remove old worktrees and data
7. **Incremental runs**: Process tasks in batches
8. **Test quality gates**: Ensure tools are installed and working

## Safety Checks

Before running in production:

1. **Backup**: Commit and push current work
2. **Review inventory**: Check discovered projects
3. **Validate task graph**: Review generated tasks
4. **Test with small batch**: Run with 10-20 tasks first
5. **Monitor closely**: Watch first few tasks complete
6. **Have rollback plan**: Know how to revert changes

## Getting Help

If issues persist:

1. Check documentation in `docs/`
2. Review error messages carefully
3. Check disk space and permissions
4. Try with reduced concurrency
5. Run demo to verify setup
6. Check GitHub issues/discussions

## Emergency Procedures

### Stop All Work

```bash
# Press Ctrl+C in terminal running swarm
# Or kill process:
pkill -f "swarm1000.swarm run"
```

### Rollback Changes

```bash
# In each worktree
cd <worktree-path>
git reset --hard HEAD~1

# Or remove worktrees entirely
git worktree list | grep swarm/ | awk '{print $1}' | xargs -I {} git worktree remove {} --force
```

### Recover from Corruption

```bash
# Remove state database
rm swarm1000/data/state.sqlite

# Remove all worktrees
git worktree prune

# Start fresh
python -m swarm1000.swarm plan --goal "..." --budget-agents 1000
python -m swarm1000.swarm run --concurrency 20
```
