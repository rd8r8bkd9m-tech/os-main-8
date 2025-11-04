#!/bin/bash
# Quickstart script for Kolibri AI Edge with scheduler demo
#
# Usage:
#   ./quickstart-agi.sh
#
# This script demonstrates:
# 1. Building the kernel and ISO
# 2. Starting QEMU with serial relay
# 3. Running the FastAPI backend with scheduler
# 4. Testing the inference endpoint with scheduler metadata logging

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="$ROOT_DIR/build"
LOGS_DIR="$ROOT_DIR/logs"
BACKEND_PORT=8000
SERIAL_PORT=5555

echo "[Kolibri AGI] Quickstart Demo"
echo "==============================================="

# Step 1: Build ISO
echo "[1/4] Building kernel and ISO..."
if [ ! -f "$BUILD_DIR/iso/kolibri.iso" ]; then
    bash "$ROOT_DIR/scripts/build_iso.sh" || {
        echo "Error: ISO build failed"
        exit 1
    }
else
    echo "  ISO already built: $BUILD_DIR/iso/kolibri.iso"
fi

# Step 2: Start QEMU in background
echo "[2/4] Starting QEMU (headless, serial relay on port $SERIAL_PORT)..."
QEMU_PID=""
if pgrep -f "qemu-system-i386.*kolibri.iso" > /dev/null 2>&1; then
    echo "  QEMU already running"
    QEMU_PID=$(pgrep -f "qemu-system-i386.*kolibri.iso" | head -1)
else
    qemu-system-i386 \
        -m 512 \
        -kernel "$BUILD_DIR/iso/kolibri.iso" \
        -serial tcp::$SERIAL_PORT,server,nowait \
        -nographic \
        -monitor none \
        -display none \
        > "$LOGS_DIR/qemu.log" 2>&1 &
    QEMU_PID=$!
    echo "  QEMU PID: $QEMU_PID"
    sleep 2
fi

# Step 3: Start backend
echo "[3/4] Starting FastAPI backend (port $BACKEND_PORT)..."
export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"
export KOLIBRI_RESPONSE_MODE=llm
export KOLIBRI_LLM_ENDPOINT="http://localhost:9000/infer"
export KOLIBRI_SSO_ENABLED=false

# Run backend in background
(
    cd "$ROOT_DIR"
    python3 -m uvicorn backend.service.app:app \
        --host 127.0.0.1 \
        --port "$BACKEND_PORT" \
        --log-level info \
        > "$LOGS_DIR/backend.log" 2>&1 &
    echo $! > "$LOGS_DIR/backend.pid"
) &
sleep 3

# Step 4: Test endpoints with scheduler
echo "[4/4] Testing inference endpoints..."
echo ""
echo "═ Health Check"
curl -s http://127.0.0.1:$BACKEND_PORT/api/health | jq .

echo ""
echo "═ Inference with Scheduler (mock LLM disabled for this test)"
echo "Testing scheduler decision metadata..."

# Create a test prompt
TEST_PROMPT="Explain energy-aware scheduling in Kolibri AI Edge"

echo ""
echo "Request: POST /api/v1/infer"
echo "Prompt: $TEST_PROMPT"
echo ""

# Make request
RESPONSE=$(curl -s -X POST \
    http://127.0.0.1:$BACKEND_PORT/api/v1/infer \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"$TEST_PROMPT\"}")

echo "Response:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"

echo ""
echo "═ Metrics"
curl -s http://127.0.0.1:$BACKEND_PORT/metrics | grep kolibri_infer | head -5

echo ""
echo "==============================================="
echo "[Kolibri AGI] Quickstart Complete"
echo ""
echo "Running services:"
echo "  - QEMU (PID $QEMU_PID): port $SERIAL_PORT"
echo "  - FastAPI Backend: http://127.0.0.1:$BACKEND_PORT"
echo ""
echo "Logs:"
echo "  - Kernel/QEMU: $LOGS_DIR/qemu.log"
echo "  - Backend: $LOGS_DIR/backend.log"
echo "  - Audit: $LOGS_DIR/audit/enterprise.log"
echo ""
echo "Try:"
echo "  curl -s http://127.0.0.1:$BACKEND_PORT/api/v1/infer \\\"
echo "    -H 'Content-Type: application/json' \\\"
echo "    -d '{\"prompt\": \"Your question here\"}'  | jq ."
echo ""
echo "To stop: kill $QEMU_PID && kill \$(cat $LOGS_DIR/backend.pid)"
echo ""

