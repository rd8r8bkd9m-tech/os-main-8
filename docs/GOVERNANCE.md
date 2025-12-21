# Governance

## Development Governance for Kolibri Swarm-1000

This document defines the rules and processes for development within the Swarm-1000 orchestrator.

## Branch Strategy

### Main Branches

- **`main`** - Production-ready code
- **`swarm/*`** - Worker branches created by orchestrator

### Branch Rules

1. **Never commit directly to `main`**
   - All changes go through worker branches
   - Pull requests required for merging

2. **Worker branches are ephemeral**
   - Created per-worker, not per-task
   - May be reused across multiple tasks
   - Can be deleted after merging

3. **Branch naming convention**
   - Worker branches: `swarm/worker-NN` (e.g., `swarm/worker-01`)
   - Manual branches: Use descriptive names

## Code Review

### Review Requirements

All code changes require review before merging:

1. **Automated reviews**
   - Quality gate checks (lint, test, build)
   - Security scans
   - Code style validation

2. **Peer reviews**
   - Assigned to reviewer agent
   - Based on reviewer skill level
   - Comments tracked in state DB

### Review Criteria

Reviewers check for:
- **Correctness**: Does it solve the problem?
- **Quality**: Does it meet coding standards?
- **Tests**: Are tests comprehensive?
- **Documentation**: Is it documented?
- **Security**: Are there vulnerabilities?
- **Performance**: Is it efficient?

### Definition of Done (DoD)

A task is complete when ALL of the following are true:

- [ ] Code implements the requirements
- [ ] All tests pass (unit, integration)
- [ ] No linting errors
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] Security scan passed
- [ ] Performance acceptable
- [ ] No blockers or dependencies

## Task Management

### Task Assignment Rules

1. **Match skills to tasks**
   - Backend tasks → Backend engineers
   - Frontend tasks → Frontend engineers
   - Security tasks → Security specialists

2. **Respect seniority**
   - Junior agents: low-risk tasks
   - Senior agents: high-risk tasks
   - Leads: architecture decisions

3. **Balance workload**
   - Distribute tasks evenly
   - Consider agent capacity
   - Avoid overloading any agent

### Task Constraints

1. **One task per commit**
   - Each task results in one commit
   - No mixing multiple tasks
   - Clear commit messages

2. **No task hoarding**
   - Complete tasks promptly
   - Don't start new tasks if blocked
   - Hand off if unable to complete

3. **Follow dependencies**
   - Never skip dependencies
   - Wait for prerequisite tasks
   - Validate dependency completion

## Quality Standards

### Code Quality

1. **Follow language-specific standards**
   - Python: PEP 8, type hints
   - JavaScript/TypeScript: ESLint, Prettier
   - Rust: Clippy, rustfmt
   - C/C++: Project style guide

2. **Write tests**
   - Unit tests for all functions
   - Integration tests for APIs
   - Edge cases covered

3. **Document everything**
   - Public APIs documented
   - Complex logic explained
   - README updated

### Energy Efficiency (Kolibri AI principle)

1. **Optimize resource usage**
   - Minimize redundant work
   - Reuse computed results
   - Efficient algorithms

2. **Avoid waste**
   - No infinite loops
   - Timeout long operations
   - Clean up resources

## Security

### Security Requirements

1. **No secrets in code**
   - Use environment variables
   - No hardcoded passwords
   - No API keys in commits

2. **Validate all inputs**
   - Sanitize user input
   - Check bounds
   - Handle errors gracefully

3. **Follow security best practices**
   - Use HTTPS
   - Encrypt sensitive data
   - Regular security audits

### Vulnerability Response

If a vulnerability is found:
1. Create high-priority task
2. Assign to security specialist
3. Fix ASAP
4. Document in changelog
5. Notify stakeholders

## Conflict Resolution

### Merge Conflicts

1. **Prevention**
   - Work in isolated worktrees
   - Small, focused changes
   - Frequent integration

2. **Resolution**
   - Manual resolution required
   - Test after resolving
   - Re-run quality gates

### Task Conflicts

If multiple agents need same resources:
1. Check task dependencies
2. Higher priority task goes first
3. Others wait or find alternative
4. Escalate to PM if needed

## Escalation

### When to Escalate

Escalate to PM/Lead when:
- Task is blocked for >1 hour
- Dependencies are unclear
- Technical decision needed
- Resource conflict
- Security concern

### Escalation Process

1. Create escalation issue
2. Tag appropriate lead
3. Provide context
4. Suggest options
5. Wait for decision

## Prohibited Actions

The following are **strictly prohibited**:

1. **Code Crimes**
   - Removing working code without reason
   - Breaking existing tests
   - Introducing security vulnerabilities
   - Ignoring quality gate failures

2. **Process Violations**
   - Skipping code review
   - Committing to main directly
   - Mixing multiple tasks in one commit
   - Ignoring dependencies

3. **Security Violations**
   - Committing secrets
   - Bypassing authentication
   - Disabling security features
   - Exposing sensitive data

Violations may result in:
- Task rejection
- Agent reassignment
- Run termination (severe cases)

## Reporting

### Progress Reporting

Report progress regularly:
- Status updates in state DB
- Commits with clear messages
- Comments on blockers
- Metrics collection

### Metrics Tracked

- Tasks completed per hour
- Quality gate pass rate
- Average task duration
- Failure rate
- Review turnaround time

## Best Practices

1. **Commit early, commit often**
   - Small, incremental changes
   - Easier to review
   - Easier to revert

2. **Test locally first**
   - Run quality gates before commit
   - Verify changes work
   - Check for regressions

3. **Communicate clearly**
   - Write descriptive commit messages
   - Comment complex code
   - Document decisions

4. **Learn and improve**
   - Review failed tasks
   - Update processes
   - Share knowledge

## Amendments

This governance document may be updated to:
- Improve processes
- Address new scenarios
- Incorporate feedback
- Align with Kolibri AI principles

All changes should be documented and communicated to all agents.
