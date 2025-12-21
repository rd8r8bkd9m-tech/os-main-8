#!/bin/bash
set -euo pipefail

# Run Codex MCP Server
# Note: This is a placeholder. Actual implementation depends on Codex installation.

PORT="${1:-8765}"

echo "=== Codex MCP Server ==="
echo "Port: $PORT"
echo ""

# Check if npx is available
if ! command -v npx &> /dev/null; then
    echo "ERROR: npx not found. Install Node.js first."
    echo ""
    echo "Alternative: Swarm will run in MOCK mode without Codex"
    exit 1
fi

# Try to start Codex MCP server
echo "Starting Codex MCP server..."
echo "Note: If codex is not installed, this will fail."
echo "Swarm will automatically fall back to MOCK mode."
echo ""

if npx -y codex mcp-server --port "$PORT" 2>/dev/null; then
    echo "Codex MCP server running on port $PORT"
else
    echo "Failed to start Codex MCP server"
    echo "Swarm will run in MOCK mode"
    exit 1
fi
