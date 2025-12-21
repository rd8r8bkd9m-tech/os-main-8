#!/bin/bash
set -euo pipefail

# Create git worktrees for swarm workers
# Usage: ./make_worktrees.sh <num_workers>

NUM_WORKERS="${1:-20}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORKSPACE_ROOT="${REPO_ROOT}-swarm"

echo "=== Creating Git Worktrees ==="
echo "Repository: $REPO_ROOT"
echo "Workspace: $WORKSPACE_ROOT"
echo "Workers: $NUM_WORKERS"
echo ""

# Create workspace directory
mkdir -p "$WORKSPACE_ROOT/workers"

# Get current branch
CURRENT_BRANCH=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)
echo "Base branch: $CURRENT_BRANCH"
echo ""

# Create worktrees
for i in $(seq -f "%02g" 1 "$NUM_WORKERS"); do
    WORKER_ID="worker-$i"
    BRANCH_NAME="swarm/$WORKER_ID"
    WORKTREE_PATH="$WORKSPACE_ROOT/workers/$WORKER_ID"
    
    if [ -d "$WORKTREE_PATH" ]; then
        echo "✓ $WORKER_ID already exists"
        continue
    fi
    
    echo "Creating $WORKER_ID..."
    
    # Create worktree with new branch
    if git -C "$REPO_ROOT" worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH" 2>/dev/null; then
        echo "✓ Created $WORKER_ID (branch: $BRANCH_NAME)"
    else
        # Branch exists, try without -b
        if git -C "$REPO_ROOT" worktree add "$WORKTREE_PATH" "$BRANCH_NAME" 2>/dev/null; then
            echo "✓ Created $WORKER_ID (existing branch)"
        else
            echo "⚠ Failed to create $WORKER_ID"
        fi
    fi
done

echo ""
echo "=== Worktree Summary ==="
git -C "$REPO_ROOT" worktree list

echo ""
echo "Worktrees created successfully!"
echo ""
echo "To remove worktrees:"
echo "  git worktree remove <path> --force"
echo ""
