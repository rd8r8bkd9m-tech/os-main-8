# 🚀 Запуск локального окружения Колибри ИИ

## Проблема
Node.js Vite dev сервер не отвечает на HTTP-запросы на этой macOS системе (таймауты на всех портах).

## Решение
Используем production build + Python HTTP сервер для frontend.

---

## 📋 Порядок запуска

### 1️⃣ Backend (FastAPI + Uvicorn)

```bash
cd "/Users/kolibri/Downloads/os-main 8"
source .chatvenv/bin/activate
KOLIBRI_SSO_ENABLED=false python -m uvicorn backend.service.app:app --host 0.0.0.0 --port 8000 --reload &
```

**Проверка**:
```bash
curl -s http://localhost:8000/docs | grep -o "<title>.*</title>"
# Должно вернуть: <title>Kolibri Enterprise API - Swagger UI</title>
```

---

### 2️⃣ Frontend (React + Vite → dist + Python)

**Сборка** (при изменениях в коде):
```bash
cd "/Users/kolibri/Downloads/os-main 8/frontend"
npm run build
```

**Запуск**:
```bash
cd "/Users/kolibri/Downloads/os-main 8/frontend/dist"
python3 -m http.server 5173 &
```

**Проверка**:
```bash
curl -s http://localhost:5173/ | grep -o "<title>.*</title>"
# Должно вернуть: <title>Колибри ИИ</title>
```

---

## 🌐 Доступ

- **Frontend UI**: http://localhost:5173/
- **API Documentation**: http://localhost:8000/docs
- **Test Page**: http://localhost:5173/test-api.html

---

## 🔧 Тестовый запрос к API

```bash
curl -X POST http://localhost:8000/api/v1/ai/reason \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Привет, Колибри!","max_tokens":100}' | jq
```

**Ожидаемый ответ**:
```json
{
  "query": "Привет, Колибри!",
  "response": "I've processed your query...",
  "confidence": 0.85,
  "mode": "script",
  "energy_cost_j": 0.05,
  "latency_ms": 0.08,
  "verified": true
}
```

---

## 🛑 Остановка

```bash
# Убить все процессы
pkill -f "uvicorn backend.service.app"
pkill -f "python3 -m http.server 5173"
```

---

## ⚙️ Изменения в коде

### Backend изменения
- ✅ Добавлен CORS middleware в `backend/service/app.py`
- ✅ SSO отключен через `KOLIBRI_SSO_ENABLED=false`

### Frontend изменения
- ✅ Исправлено: `query` → `prompt` в API запросе
- ✅ Добавлена обработка ошибок HTTP
- ✅ Минимальный набор зависимостей (60 пакетов)

---

## 📝 Известные проблемы

1. **Vite dev server не работает**: Висит на всех HTTP-запросах (macOS системная проблема)
   - **Обходной путь**: Используем production build + Python HTTP сервер

2. **CORS**: Настроен только для `localhost:5173`
   - Для других портов добавьте в `allow_origins` в `backend/service/app.py`

3. **Авторизация**: Отключена для dev-режима
   - В production используйте `KOLIBRI_SSO_ENABLED=true` и передавайте Bearer token

---

## ✅ Проверка работоспособности

### 1. Проверить процессы
```bash
lsof -i :8000 | grep LISTEN  # Backend
lsof -i :5173 | grep LISTEN  # Frontend
```

### 2. Открыть в браузере
```bash
open http://localhost:5173/
```

### 3. Протестировать AI запрос через UI
- Введите текст в поле
- Нажмите "Отправить"
- Должен появиться ответ от AI

---

## 🔄 Быстрый перезапуск

```bash
# Все в одном скрипте
cd "/Users/kolibri/Downloads/os-main 8"

# Убить старые процессы
pkill -f uvicorn; pkill -f "http.server 5173"; sleep 2

# Запустить backend
source .chatvenv/bin/activate
KOLIBRI_SSO_ENABLED=false python -m uvicorn backend.service.app:app --host 0.0.0.0 --port 8000 --reload &

# Пересобрать и запустить frontend
cd frontend && npm run build
cd dist && python3 -m http.server 5173 &

# Подождать и открыть браузер
sleep 3
open http://localhost:5173/
```

---

## 📞 Поддержка

При проблемах проверьте:
1. Активирован ли venv: `which python` должен показать `.chatvenv/bin/python`
2. Свободны ли порты: `lsof -i :8000` и `lsof -i :5173`
3. Логи backend: добавьте `2>&1 | tee backend.log` к команде uvicorn
