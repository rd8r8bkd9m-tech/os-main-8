#!/bin/bash
set -euo pipefail

# Kolibri Swarm-1000 Demo Script (Non-interactive for CI/Testing)
# Demonstrates the complete workflow: inventory -> plan -> run -> report

echo "=========================================="
echo "  Kolibri Swarm-1000 Orchestrator Demo"
echo "=========================================="
echo ""

# Get repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "Repository: $REPO_ROOT"
echo ""

# Clean previous run
rm -f swarm1000/data/state.sqlite

# Step 1: Inventory
echo "=== Step 1: Inventory ==="
echo "Scanning current repository..."
python -m swarm1000.swarm inventory \
    --roots "$REPO_ROOT" \
    --max-depth 2

echo ""

# Step 2: Plan
echo "=== Step 2: Plan ==="
echo "Generating task plan for 20 tasks..."
python -m swarm1000.swarm plan \
    --goal "Demo: Build unified Kolibri platform" \
    --budget-agents 20

echo ""

# Step 3: Run
echo "=== Step 3: Run ==="
echo "Executing tasks with 3 concurrent workers..."
echo "Note: This is a DEMO with MOCK mode enabled"
echo ""

python -m swarm1000.swarm run \
    --concurrency 3 \
    --mode single \
    --quality-gate skip

echo ""

# Step 4: Report
echo "=== Step 4: Report ==="
python -m swarm1000.swarm status

echo ""
echo "Exporting results..."
python -m swarm1000.swarm export \
    --output swarm1000/data/demo_results.json

echo ""
echo "=========================================="
echo "  Demo Complete!"
echo "=========================================="
echo ""
echo "Results exported to: swarm1000/data/demo_results.json"
echo ""
echo "Summary:"
cat swarm1000/data/demo_results.json | python -m json.tool | grep -E '"total_tasks"|"status": "completed"' | head -5
echo ""
