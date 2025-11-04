#!/bin/bash
# Kolibri AI System — Server Startup Script

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       KOLIBRI AI SYSTEM — Server Startup                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Activate virtual environment
echo "🔧 Activating Python environment..."
if [ -d ".chatvenv" ]; then
    source .chatvenv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ Error: Virtual environment not found"
    echo "   Create it with: python -m venv .chatvenv"
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt 2>/dev/null || true

# Start server
echo ""
echo "🚀 Starting Kolibri AI server..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Server running on:"
echo "   • API: http://localhost:8000"
echo "   • Docs: http://localhost:8000/docs"
echo "   • ReDoc: http://localhost:8000/redoc"
echo ""
echo "📚 Documentation:"
echo "   • Quick Start: KOLIBRI_AI_QUICKSTART.md"
echo "   • Full Spec: KOLIBRI_AI_IMPLEMENTATION.md"
echo "   • Running: SYSTEM_RUNNING.md"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run server
python -m uvicorn backend.service.main:app --host 0.0.0.0 --port 8000 --reload

