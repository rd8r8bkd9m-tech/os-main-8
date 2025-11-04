#!/bin/bash

# System Health Check & Diagnostics
# Проверяет все компоненты системы Kolibri-Omega

set -e

echo "🔍 Диагностика системы Kolibri-Omega ИИ"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_port() {
    local port=$1
    local name=$2
    if lsof -i :$port 2>/dev/null | grep -q LISTEN; then
        echo -e "${GREEN}✅${NC} $name работает (порт $port)"
        return 0
    else
        echo -e "${RED}❌${NC} $name не запущен (порт $port)"
        return 1
    fi
}

check_binary() {
    local path=$1
    local name=$2
    if [ -x "$path" ]; then
        size=$(du -h "$path" | cut -f1)
        echo -e "${GREEN}✅${NC} $name найден ($size)"
        return 0
    else
        echo -e "${RED}❌${NC} $name не найден"
        return 1
    fi
}

check_http() {
    local url=$1
    local name=$2
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $name отвечает"
        return 0
    else
        echo -e "${RED}❌${NC} $name не отвечает"
        return 1
    fi
}

# 1. Check C Engine
echo "📦 C Engine:"
check_binary "/Users/kolibri/Downloads/os-main 8/build-fuzz/kolibri_sim" "kolibri_sim"
echo ""

# 2. Check processes
echo "🔌 Запущенные процессы:"
check_port 8000 "API Bridge (FastAPI)" || true
check_port 5173 "Frontend (Vite)" || true
echo ""

# 3. Check HTTP endpoints
echo "🌐 HTTP Endpoints:"
check_http "http://localhost:8000/health" "API Health" || true
check_http "http://localhost:8000/docs" "API Docs" || true
check_http "http://localhost:5173" "Frontend" || true
echo ""

# 4. API Response test
echo "📊 API Response Test:"
if check_http "http://localhost:8000/health" "Health Check"; then
    health=$(curl -s http://localhost:8000/health)
    echo "   Response: $health"
    echo ""
fi

# 5. Reasoning endpoint test
echo "🧠 AI Reasoning Test:"
if curl -s http://localhost:8000/health > /dev/null; then
    response=$(curl -s -X POST http://localhost:8000/api/v1/ai/reason \
        -H "Content-Type: application/json" \
        -d '{"prompt":"Test","max_tokens":100}')
    
    status=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")
    phases=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['phases_executed']))" 2>/dev/null || echo "0")
    
    if [ "$status" = "success" ]; then
        echo -e "${GREEN}✅${NC} Reasoning работает"
        echo "   Status: $status"
        echo "   Phases executed: $phases"
    fi
    echo ""
fi

# 6. Stats endpoint test
echo "📈 Statistics Endpoint:"
if curl -s http://localhost:8000/health > /dev/null; then
    stats=$(curl -s http://localhost:8000/api/v1/ai/generative/stats)
    queries=$(echo "$stats" | python3 -c "import sys, json; print(json.load(sys.stdin)['queries_processed'])" 2>/dev/null || echo "0")
    generation=$(echo "$stats" | python3 -c "import sys, json; print(json.load(sys.stdin)['formula_pool']['generation'])" 2>/dev/null || echo "0")
    
    echo -e "${GREEN}✅${NC} Stats работают"
    echo "   Queries processed: $queries"
    echo "   Generation: $generation"
    echo ""
fi

# 7. Environment check
echo "🛠 Окружение:"
python_version=$(.chatvenv/bin/python --version 2>/dev/null || echo "не установлен")
echo "   Python: $python_version"

node_version=$(node --version 2>/dev/null || echo "не установлен")
echo "   Node.js: $node_version"

cmake_version=$(cmake --version 2>/dev/null | head -1 || echo "не установлен")
echo "   CMake: $cmake_version"
echo ""

# Summary
echo "=========================================="
echo "📋 Диагностика завершена"
echo ""
echo "💡 Для запуска системы используйте:"
echo "   ./run_system.sh"
echo ""
echo "📖 Или вручную:"
echo "   Terminal 1: .chatvenv/bin/python api_bridge.py"
echo "   Terminal 2: cd frontend && npm run dev"
echo ""
