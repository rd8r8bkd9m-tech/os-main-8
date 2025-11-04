#!/usr/bin/env bash
# Запуск полной системы Kolibri-Omega:
# 1. Backend API Bridge (Python/FastAPI)
# 2. Frontend React (Vite)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🐦 Kolibri-Omega System Launcher"
echo "================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

# Check Node.js for frontend
if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js not found (frontend will not start)"
    SKIP_FRONTEND=1
fi

echo ""
echo "📦 Используем виртуальное окружение Python..."

# Используем venv если доступен
if [ -f ".chatvenv/bin/python" ]; then
    PYTHON_CMD=".chatvenv/bin/python"
    echo "✅ Виртуальное окружение найдено"
else
    PYTHON_CMD="python3"
    echo "⚠️  Используется системный Python"
fi

# Start API Bridge in background
echo ""
echo "🚀 Запуск API Bridge на http://localhost:8000..."
$PYTHON_CMD api_bridge.py &
API_PID=$!
echo "   API PID: $API_PID"

# Wait for API to be ready
sleep 3

# Check if API is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ API Bridge failed to start"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

echo "✅ API Bridge ready"

# Start frontend if Node.js available
if [ -z "$SKIP_FRONTEND" ]; then
    echo ""
    echo "📦 Installing frontend dependencies..."
    cd frontend
    if [ -d "node_modules" ]; then
        echo "   (dependencies already cached)"
    else
        npm install -q
    fi
    
    echo ""
    echo "🎨 Starting Frontend on http://localhost:5173..."
    npm run dev &
    FRONTEND_PID=$!
    echo "   Frontend PID: $FRONTEND_PID"
    
    sleep 2
fi

echo ""
echo "================================"
echo "✅ System Running:"
echo ""
echo "   🔗 API Bridge:  http://localhost:8000"
echo "   🎨 Frontend:    http://localhost:5173"
echo "   📖 API Docs:    http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "================================"
echo ""

# Handle cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $API_PID 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Shutdown complete"
}

trap cleanup EXIT INT TERM

# Wait for processes
wait
