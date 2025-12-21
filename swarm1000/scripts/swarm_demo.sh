#!/bin/bash
set -euo pipefail

# Kolibri Swarm-1000 Demo Script
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

# Step 1: Inventory
echo "=== Step 1: Inventory ==="
echo "Scanning current repository..."
python -m swarm1000.swarm inventory \
    --roots "$REPO_ROOT" \
    --max-depth 3

echo ""
read -p "Press Enter to continue to planning..."
echo ""

# Step 2: Plan
echo "=== Step 2: Plan ==="
echo "Generating task plan for 50 tasks..."
python -m swarm1000.swarm plan \
    --goal "Demo: Build unified Kolibri platform" \
    --budget-agents 50

echo ""
read -p "Press Enter to continue to execution..."
echo ""

# Step 3: Run
echo "=== Step 3: Run ==="
echo "Executing tasks with 5 concurrent workers..."
echo "Note: This is a DEMO with MOCK mode enabled"
echo ""

python -m swarm1000.swarm run \
    --concurrency 5 \
    --mode single \
    --quality-gate skip

echo ""
read -p "Press Enter to see report..."
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
echo "Next steps:"
echo "  - Review task graph: swarm1000/data/task_graph.json"
echo "  - Review personas: swarm1000/data/personas_1000.jsonl"
echo "  - Run with more concurrency: python -m swarm1000.swarm run --concurrency 20"
echo ""
