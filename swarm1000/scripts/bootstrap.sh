#!/bin/bash
set -euo pipefail

# Kolibri Swarm-1000 Bootstrap Script
# Sets up the environment for swarm orchestrator

echo "=== Kolibri Swarm-1000 Bootstrap ==="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if Python 3.10+
required_version="3.10"
if ! python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo "ERROR: Python 3.10+ required"
    exit 1
fi

echo "✓ Python version OK"
echo ""

# Check Git
echo "Checking Git..."
if ! command -v git &> /dev/null; then
    echo "ERROR: Git not found"
    exit 1
fi

git_version=$(git --version)
echo "$git_version"
echo "✓ Git OK"
echo ""

# Create data directory
echo "Creating data directory..."
mkdir -p swarm1000/data
echo "✓ Data directory created"
echo ""

# Check optional tools
echo "Checking optional tools..."

if command -v ruff &> /dev/null; then
    echo "✓ ruff available"
else
    echo "⚠ ruff not found (optional, for Python linting)"
fi

if command -v pytest &> /dev/null; then
    echo "✓ pytest available"
else
    echo "⚠ pytest not found (optional, for Python testing)"
fi

if command -v npm &> /dev/null; then
    echo "✓ npm available"
else
    echo "⚠ npm not found (optional, for JavaScript/TypeScript)"
fi

if command -v cargo &> /dev/null; then
    echo "✓ cargo available"
else
    echo "⚠ cargo not found (optional, for Rust)"
fi

echo ""
echo "=== Bootstrap Complete ==="
echo ""
echo "Next steps:"
echo "  1. Run: python -m swarm1000.swarm --help"
echo "  2. Run demo: ./swarm1000/scripts/swarm_demo.sh"
echo ""
