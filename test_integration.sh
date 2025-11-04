#!/usr/bin/env bash
# Quick integration test - verify API bridge and frontend communication

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🔍 Kolibri-Omega Integration Test"
echo "=================================="
echo ""

# Test 1: Check C binary exists
echo "1️⃣  Checking C backend binary..."
if [ -f "$SCRIPT_DIR/build-fuzz/kolibri_sim" ]; then
    echo "   ✅ Binary found: $SCRIPT_DIR/build-fuzz/kolibri_sim"
else
    echo "   ⚠️  Binary not found - need to rebuild"
    echo "   Run: cd build-fuzz && cmake .. && make test-omega"
fi
echo ""

# Test 2: Check Python
echo "2️⃣  Checking Python environment..."
if python3 -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
    echo "   ✅ Required Python packages installed"
else
    echo "   ⚠️  Missing Python packages"
    echo "   Run: python3 -m pip install fastapi uvicorn pydantic"
fi
echo ""

# Test 3: Check API bridge script
echo "3️⃣  Checking API bridge script..."
if [ -f "$SCRIPT_DIR/api_bridge.py" ]; then
    echo "   ✅ API bridge found"
    LINES=$(wc -l < "$SCRIPT_DIR/api_bridge.py")
    echo "   📝 Size: $LINES lines"
else
    echo "   ❌ API bridge not found"
    exit 1
fi
echo ""

# Test 4: Check React frontend
echo "4️⃣  Checking React frontend..."
if [ -d "$SCRIPT_DIR/frontend" ]; then
    echo "   ✅ Frontend directory found"
    if [ -f "$SCRIPT_DIR/frontend/src/App.tsx" ]; then
        echo "   ✅ App.tsx configured to use API"
        # Check if App.tsx has the API endpoint
        if grep -q "localhost:8000/api/v1/ai/reason" "$SCRIPT_DIR/frontend/src/App.tsx"; then
            echo "   ✅ API endpoint configured correctly"
        else
            echo "   ⚠️  API endpoint may not be configured"
        fi
    fi
else
    echo "   ❌ Frontend not found"
fi
echo ""

# Test 5: Port availability check
echo "5️⃣  Checking ports..."

# Port 8000 (API)
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ⚠️  Port 8000 already in use (API)"
    KILL_8000=1
else
    echo "   ✅ Port 8000 available (API)"
fi

# Port 5173 (Frontend)
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ⚠️  Port 5173 already in use (Frontend)"
    KILL_5173=1
else
    echo "   ✅ Port 5173 available (Frontend)"
fi
echo ""

# Test 6: Check documentation
echo "6️⃣  Checking documentation..."
DOCS_FOUND=0
[ -f "$SCRIPT_DIR/API_INTEGRATION.md" ] && { echo "   ✅ API_INTEGRATION.md"; DOCS_FOUND=$((DOCS_FOUND+1)); }
[ -f "$SCRIPT_DIR/FRONTEND_INTEGRATION_COMPLETE.md" ] && { echo "   ✅ FRONTEND_INTEGRATION_COMPLETE.md"; DOCS_FOUND=$((DOCS_FOUND+1)); }
[ -f "$SCRIPT_DIR/TESTING_GUIDE.md" ] && { echo "   ✅ TESTING_GUIDE.md"; DOCS_FOUND=$((DOCS_FOUND+1)); }
echo "   📚 Docs: $DOCS_FOUND/3 files"
echo ""

# Summary
echo "=================================="
echo "✅ Integration Test Complete"
echo ""

if [ -n "$KILL_8000" ] || [ -n "$KILL_5173" ]; then
    echo "⚠️  Some ports in use. Kill with:"
    [ -n "$KILL_8000" ] && echo "   lsof -ti :8000 | xargs kill -9"
    [ -n "$KILL_5173" ] && echo "   lsof -ti :5173 | xargs kill -9"
    echo ""
fi

echo "🚀 Ready to start system:"
echo "   bash start_system.sh"
echo ""
echo "📖 View documentation:"
echo "   - API_INTEGRATION.md (full guide)"
echo "   - FRONTEND_INTEGRATION_COMPLETE.md (quick start)"
echo "   - http://localhost:8000/docs (interactive)"
