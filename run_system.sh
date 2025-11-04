#!/bin/bash

# Kolibri-Omega Complete System Launcher
# Запускает всю систему: API Bridge + React Frontend

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🐦 Запуск Kolibri-Omega ИИ Системы..."
echo ""

# Kill any existing processes on ports 8000 and 5173
echo "🧹 Очистка портов..."
lsof -i :8000 2>/dev/null | awk 'NR>1 {print $2}' | xargs kill -9 2>/dev/null || true
lsof -i :5173 2>/dev/null | awk 'NR>1 {print $2}' | xargs kill -9 2>/dev/null || true
sleep 1

# Start API Bridge (Python FastAPI)
echo "⚙️  Запуск API Bridge (FastAPI)..."
.chatvenv/bin/python api_bridge.py > /tmp/api.log 2>&1 &
API_PID=$!
sleep 2

# Verify API is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API Bridge запущен (PID: $API_PID)"
else
    echo "❌ API Bridge не запустился!"
    cat /tmp/api.log
    exit 1
fi

# Start React Frontend (Vite)
echo "🎨 Запуск React Frontend (Vite)..."
cd frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 3

# Verify Frontend is running
if lsof -i :5173 2>/dev/null | grep -q LISTEN; then
    echo "✅ Frontend запущен (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend не запустился!"
    cat /tmp/frontend.log
    exit 1
fi

echo ""
echo "========================================="
echo "🐦 Система запущена успешно!"
echo "========================================="
echo ""
echo "📱 Фронтенд:  http://localhost:5173"
echo "⚙️  API:      http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Нажмите Ctrl+C для остановки системы"
echo ""

# Wait for interrupt
wait
