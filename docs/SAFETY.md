# Safety Protocols

## Core Safety Principles

The Kolibri Swarm-1000 Orchestrator follows strict safety protocols to prevent accidental damage to code, data, and systems.

## Non-Destructive Operations

### What We NEVER Do

The orchestrator **will never** perform these operations without explicit approval:

1. **Delete files outside the repository**
   - Will not `rm` files in external paths
   - Will not remove user directories
   - Will not delete system files

2. **Move files outside the repository**
   - Will not `mv` files to external locations
   - Will not reorganize user directories
   - Will not rename external projects

3. **Modify permissions broadly**
   - Will not `chmod -R` on external paths
   - Will not change ownership of system files
   - Will not modify executable permissions without reason

4. **Mass operations on external paths**
   - Will not batch rename files in user directories
   - Will not bulk delete across multiple projects
   - Will not modify configuration files globally

### Workspace Boundaries

**All operations are confined to**:
- The current repository
- Created git worktrees
- Swarm data directory (`swarm1000/data/`)

**Never modified**:
- Parent directories
- User home directory
- System directories
- External project directories (except during inventory scan, which is read-only)

## DRY RUN Mode

### Dangerous Operations

For potentially destructive operations, the system uses **DRY RUN** mode:

1. **Analyze** the operation
2. **Report** what would be changed
3. **Wait** for explicit approval
4. **Execute** only after confirmation

### Example: Mass Rename

```bash
# System detects mass rename request
[DRY RUN] The following files would be renamed:
  - file1.txt -> file1_new.txt
  - file2.txt -> file2_new.txt
  ... (48 more)

Confirm? (yes/no):
```

User must type "yes" explicitly. Any other input cancels.

### Operations Requiring DRY RUN

- Renaming >10 files
- Deleting >5 files
- Moving files across directories
- Changing >20 file permissions
- Modifying configuration files

## Secret Protection

### No Secrets in Logs

The orchestrator **never logs**:
- Passwords
- API keys
- Tokens
- Private keys
- Environment variables from `.env`

### No Secrets in Commits

The orchestrator **validates** before commit:
- No files containing patterns like `password=`, `api_key=`
- `.env` files are in `.gitignore`
- No private key files (`.pem`, `.key`)
- No credential files

### Environment Variables

`.env` files are:
- Respected by `.gitignore`
- Never committed
- Never logged
- Never shared across workers

## Code Safety

### Only Modify Repository Code

**Allowed**:
- Editing files in the current repository
- Creating new files in the repository
- Deleting files in the repository (with validation)

**Not allowed**:
- Modifying files outside repository
- Editing system configurations
- Changing external dependencies

### Quality Gates Prevent Breaking Changes

Before committing, quality gates check:
1. **Syntax**: Code parses correctly
2. **Linting**: No style violations
3. **Tests**: All tests still pass
4. **Build**: Project still builds

If any check fails:
- Changes are **not committed**
- Task is marked as failed
- Error is logged for review

### Rollback Capability

Every change is:
- Made in isolated worktree
- Committed to worker branch
- Reviewable before merge
- Revertable via git

## Concurrency Safety

### Worker Isolation

Each worker operates in:
- Separate git worktree
- Separate branch
- Isolated file system namespace

Workers **cannot**:
- Interfere with each other
- Share mutable state
- Cause race conditions

### Resource Limits

To prevent system overload:
- **Max concurrency**: 100 workers
- **Default concurrency**: 20 workers
- **Timeout on external commands**: 30-120 seconds
- **File size limits**: 5MB for reads

### Database Locking

SQLite state database uses:
- Transaction isolation
- Automatic retry on lock
- Timeout after 5 seconds

## Security Safety

### Input Validation

All user inputs are validated:
- **Paths**: Must be absolute, must exist
- **Counts**: Must be positive integers
- **Modes**: Must be from allowed set
- **Goals**: Sanitized before use

### Command Injection Prevention

Never execute user input directly:
- All shell commands use argument arrays
- No string interpolation in commands
- Subprocess calls with explicit arguments

Example (SAFE):
```python
subprocess.run(["git", "add", user_file], check=True)
```

Example (UNSAFE - NOT USED):
```python
os.system(f"git add {user_file}")  # NEVER DONE
```

### Sandbox Constraints

Operations are sandboxed to:
- `workspace-write`: Can modify worktree
- `workspace-read`: Can only read worktree
- `none`: No file system access

## Data Safety

### State Persistence

All progress is saved to SQLite:
- Tasks and status
- Commits
- Failures
- Metrics

If interrupted:
- State is preserved
- Can resume from last checkpoint
- No data loss

### Backup Recommendations

Before running swarm:
1. **Commit all changes**: `git commit -am "Before swarm"`
2. **Push to remote**: `git push`
3. **Tag snapshot**: `git tag swarm-before-$(date +%Y%m%d)`

### Recovery Procedures

If something goes wrong:

1. **Stop execution**: Ctrl+C or kill process
2. **Check state**: `python -m swarm1000.swarm status`
3. **Review changes**: Check worktree branches
4. **Rollback if needed**: Remove worktrees, reset state
5. **Report issue**: Document what happened

## Network Safety

### No Unauthorized Network Access

The orchestrator:
- Does not phone home
- Does not send telemetry
- Does not access external APIs (except Codex MCP if configured)
- Does not download code without approval

### Codex MCP Safety

When using Codex MCP:
- Code changes are reviewed before commit
- Quality gates validate changes
- Mock mode available for testing
- Can be disabled entirely

## Compliance

### Respect .gitignore

The orchestrator respects `.gitignore`:
- Does not commit ignored files
- Does not track ignored patterns
- Adds own exclusions for:
  - `swarm1000/data/state.sqlite`
  - `swarm1000/data/*.log`

### License Compliance

Does not:
- Copy copyrighted code
- Use proprietary code without permission
- Violate open source licenses

## Monitoring and Auditing

### Audit Trail

All actions are logged:
- Task assignments
- Changes made
- Commits created
- Failures encountered

Logs include:
- Timestamp
- Agent ID
- Task ID
- Action type
- Result

### Tamper Detection

The system tracks:
- Unexpected file changes
- Manual modifications during run
- External git operations

Warns if detected.

## Emergency Procedures

### Immediate Stop

If you need to stop immediately:

```bash
# Press Ctrl+C
# Or kill the process
pkill -f "swarm1000.swarm run"
```

Progress is saved. Can resume later.

### Emergency Rollback

To undo all changes:

```bash
# Remove all worktrees
git worktree list | grep swarm/ | awk '{print $1}' | \
  xargs -I {} git worktree remove {} --force

# Delete worker branches
git branch | grep swarm/ | xargs git branch -D

# Reset state
rm swarm1000/data/state.sqlite
```

### Quarantine

If a worker makes suspicious changes:

```bash
# Don't merge that worktree
# Inspect the changes
cd <worktree-path>
git diff HEAD~1

# If bad, remove it
git worktree remove <worktree-path> --force
```

## User Responsibilities

Users must:

1. **Review before merging**
   - Check worktree branches
   - Review commits
   - Test changes locally

2. **Monitor execution**
   - Watch for errors
   - Check resource usage
   - Verify expected behavior

3. **Report issues**
   - Document problems
   - Share logs
   - Help improve safety

4. **Follow guidelines**
   - Read documentation
   - Use appropriate settings
   - Test in safe environment first

## Safety Checklist

Before running swarm in production:

- [ ] Repository is backed up
- [ ] Changes are committed
- [ ] Remote is up to date
- [ ] Have reviewed task graph
- [ ] Understand the goal
- [ ] Tested with small batch first
- [ ] Monitoring in place
- [ ] Know how to stop
- [ ] Know how to rollback
- [ ] Read this safety document

## Continuous Improvement

This safety document is:
- Living documentation
- Updated based on incidents
- Improved with user feedback
- Aligned with Kolibri AI principles

Report safety concerns to help make the system safer for everyone.

## Summary

**The Kolibri Swarm-1000 Orchestrator is designed to be safe by default:**

✓ Operates only within repository boundaries  
✓ Uses DRY RUN for dangerous operations  
✓ Validates all changes with quality gates  
✓ Isolates workers in separate worktrees  
✓ Protects secrets and credentials  
✓ Logs all actions for audit  
✓ Preserves state for recovery  
✓ Respects system and user boundaries  

**When in doubt, the system errs on the side of caution.**
