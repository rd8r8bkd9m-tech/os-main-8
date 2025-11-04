#!/bin/bash
set -e

echo "🧹 Генеральная уборка проекта Kolibri ИИ"
echo "==========================================="

# 1. Убиваем все процессы
echo "1️⃣ Убиваю процессы..."
pkill -f "python api_bridge" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "node" 2>/dev/null || true
sleep 1

# 2. Очищаю Python кэш
echo "2️⃣ Очищаю Python кэш..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name ".coverage" -delete 2>/dev/null || true

# 3. Очищаю мусор OS
echo "3️⃣ Очищаю мусор OS..."
find . -type f -name ".DS_Store" -delete 2>/dev/null || true
find . -type f -name "*.swp" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true

# 4. Очищаю лог файлы
echo "4️⃣ Очищаю логи..."
rm -f /tmp/api.log /tmp/frontend.log /tmp/*.log 2>/dev/null || true
rm -f logs/*.log 2>/dev/null || true

# 5. Очищаю временные файлы
echo "5️⃣ Очищаю временные файлы..."
rm -f nohup.out 2>/dev/null || true
rm -f *.pid 2>/dev/null || true
rm -rf /tmp/kolibri* 2>/dev/null || true

# 6. Очищаю Node кэш
echo "6️⃣ Очищаю Node кэш..."
rm -rf frontend/node_modules/.cache 2>/dev/null || true
rm -rf .npm 2>/dev/null || true

echo ""
echo "✅ Генеральная уборка завершена!"
echo ""
echo "📊 Статистика проекта:"
du -sh . 2>/dev/null | awk '{print "Размер проекта: " $1}'
find . -type f -name "*.c" -o -name "*.h" | wc -l | awk '{print "C/H файлов: " $1}'
find . -type f -name "*.py" | wc -l | awk '{print "Python файлов: " $1}'
find . -type f -name "*.tsx" -o -name "*.ts" | wc -l | awk '{print "TypeScript файлов: " $1}'
