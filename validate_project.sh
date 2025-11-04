#!/bin/bash
# Quick validation script after project cleanup
# Run this to ensure everything is in order

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔍 Kolibri OS — Project Validation ($(date))"
echo "================================================"
echo ""

# 1. Check Python environment
echo "✓ Checking Python environment..."
if [ -d .chatvenv ]; then
    PYTHON=".chatvenv/bin/python"
else
    PYTHON="python"
fi

$PYTHON -c "import sys; print(f'  Python {sys.version.split()[0]}')" 2>/dev/null || {
    echo "  ⚠️  Python not found. Please run: python -m venv .chatvenv && source .chatvenv/bin/activate"
    exit 1
}

# 2. Check key modules
echo ""
echo "✓ Checking backend modules..."
$PYTHON -c "from backend.service.scheduler import EnergyAwareScheduler; print('  ✅ EnergyAwareScheduler')" 2>/dev/null
$PYTHON -c "from backend.service.plugins.persistent_runner import MockPersistentRunner; print('  ✅ MockPersistentRunner')" 2>/dev/null
$PYTHON -c "from backend.service.tools.snapshot import Snapshot, SnapshotClaim; print('  ✅ Snapshot tools')" 2>/dev/null

# 3. Check documentation
echo ""
echo "✓ Checking documentation..."
for file in projects/kolibri_ai_edge/README.md projects/kolibri_ai_edge/AGI_MANIFESTO.md projects/kolibri_ai_edge/AGI_ARCHITECTURE.md projects/kolibri_ai_edge/IP_README.md PROJECT_STATUS.md CLEANUP_SUMMARY.md; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo "  ✅ $file ($lines lines)"
    fi
done

# 4. Check build artifacts
echo ""
echo "✓ Checking build status..."
if [ -d build ]; then
    iso_file="build/kolibri.iso"
    if [ -f "$iso_file" ]; then
        size=$(du -h "$iso_file" | cut -f1)
        echo "  ✅ ISO ready ($size)"
    else
        echo "  ⚠️  ISO not built. Run: ./scripts/build_iso.sh"
    fi
else
    echo "  ⚠️  build/ directory not found. Build not complete."
fi

# 5. Test status
echo ""
echo "✓ Running quick smoke test..."
$PYTHON -c "
from backend.service.scheduler import EnergyAwareScheduler
scheduler = EnergyAwareScheduler(upstream_available=True)
choice = scheduler.schedule('Hello world')
print(f'  ✅ Scheduler routing: {choice.runner_type}')
" 2>/dev/null

echo ""
echo "================================================"
echo "✅ Project validation complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Backend:  ./scripts/run_backend.sh --port 8080"
echo "  2. ISO:      qemu-system-i386 -cdrom build/kolibri.iso"
echo "  3. Tests:    pytest tests/ -q"
echo "  4. Docs:     cat PROJECT_STATUS.md"
echo ""
