# 🐦 Колибри-Omega ИИ — Полная интеграция

Генеративная 10-фазная система с web-интерфейсом и API.

## 🎯 Компоненты системы

| Компонент | Язык | Фреймворк | Порт | Статус |
|-----------|------|-----------|------|--------|
| **C Engine** | C | Native | — | ✅ 10 фаз, работает |
| **API Bridge** | Python | FastAPI | 8000 | ✅ Работает |
| **Frontend** | TypeScript | React + Vite | 5173 | ✅ Работает |

## 🚀 Быстрый старт

### Способ 1: Автоматический запуск

```bash
cd "/Users/kolibri/Downloads/os-main 8"
./run_system.sh
```

Откройте в браузере: **http://localhost:5173**

### Способ 2: Ручной запуск

#### 1️⃣ Запуск API Bridge (Terminal 1)
```bash
cd "/Users/kolibri/Downloads/os-main 8"
.chatvenv/bin/python api_bridge.py
```

#### 2️⃣ Запуск Frontend (Terminal 2)
```bash
cd "/Users/kolibri/Downloads/os-main 8/frontend"
npm run dev
```

#### 3️⃣ Откройте браузер
```
http://localhost:5173
```

## 📖 API Documentation

### Health Check
```bash
curl http://localhost:8000/health
```
**Response:** `{"status":"ready","engine_running":true}`

### AI Reasoning Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/ai/reason \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Как работает Колибри?","max_tokens":1000}'
```

### Generative Stats
```bash
curl http://localhost:8000/api/v1/ai/generative/stats
```

### Interactive API Docs
```
http://localhost:8000/docs
```

## 🔧 Архитектура

```
┌─────────────────────────────────────────────────────┐
│          React Frontend (Vite)                      │
│          localhost:5173                             │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP/JSON
                  ▼
┌─────────────────────────────────────────────────────┐
│          FastAPI Bridge                             │
│          localhost:8000                             │
│  • CORS enabled for localhost:5173                  │
│  • Response models with Pydantic                    │
└─────────────────┬───────────────────────────────────┘
                  │ subprocess
                  ▼
┌─────────────────────────────────────────────────────┐
│          Kolibri-Omega C Engine                     │
│          10-Phase Generative System                 │
│                                                     │
│  Phase 1:  Cognitive Lobes                         │
│  Phase 2:  Reasoning Engine                        │
│  Phase 3:  Pattern Detection                       │
│  Phase 4:  Hierarchy                               │
│  Phase 5:  Coordination                            │
│  Phase 6:  Counterfactuals                         │
│  Phase 7:  Adaptation                              │
│  Phase 8:  Policy Learning                         │
│  Phase 9:  Bayesian Networks                       │
│  Phase 10: Scenario Planning                       │
└─────────────────────────────────────────────────────┘
```

## 📊 Features

- ✅ **10-Phase AI Engine**: Полная когнитивная архитектура
- ✅ **REST API**: Полностью типизированные endpoints
- ✅ **React UI**: Современный интерфейс с Vite HMR
- ✅ **Live Stats**: Отслеживание генерации и примеров
- ✅ **CORS**: Готово к интеграции с другими фронтендами
- ✅ **Логирование**: Подробные логи всех операций

## 🛠 Команды разработки

### Пересборка C Engine
```bash
cd build-fuzz
cmake ..
make -j4 kolibri_sim
```

### Проверка Python типов
```bash
cd "/Users/kolibri/Downloads/os-main 8"
.chatvenv/bin/python -m pyright api_bridge.py
```

### Очистка портов (если зависли)
```bash
lsof -i :8000 | awk 'NR>1 {print $2}' | xargs kill -9
lsof -i :5173 | awk 'NR>1 {print $2}' | xargs kill -9
```

## 📝 Примеры использования

### JavaScript/TypeScript
```typescript
const response = await fetch('http://localhost:8000/api/v1/ai/reason', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    prompt: "Объясни Колибри",
    max_tokens: 1000
  })
});
const data = await response.json();
console.log(data.reasoning.phases);
```

### Python
```python
import requests

response = requests.post('http://localhost:8000/api/v1/ai/reason', json={
    'prompt': 'Как работает система?',
    'max_tokens': 1000
})
print(response.json()['reasoning'])
```

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/ai/reason \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Привет колибри","max_tokens":1000}' | jq .
```

## 📦 Project Structure

```
os-main 8/
├── api_bridge.py              # FastAPI Gateway
├── kolibri.sh                 # Original launcher
├── run_system.sh              # New system launcher ✨
├── requirements.txt           # Python deps
├── .chatvenv/                 # Python venv
├── build-fuzz/                # CMake build dir
│   └── kolibri_sim            # Compiled C binary
├── frontend/                  # React + Vite
│   ├── src/
│   │   ├── App.tsx            # Main component
│   │   ├── Stats.tsx          # Statistics panel
│   │   └── TeachMode.tsx      # Teaching mode
│   ├── package.json
│   └── vite.config.ts
├── apps/                      # C source
├── core/                      # Python core
└── README.md
```

## 🔍 Troubleshooting

### "Port 8000 already in use"
```bash
lsof -i :8000 | awk 'NR>1 {print $2}' | xargs kill -9
```

### "Frontend shows loading but no response"
1. Откройте F12 (Developer Tools)
2. Проверьте консоль на ошибки
3. Проверьте Network tab — запрос должен вернуть 200

### "API returns 503"
API требует C engine. Проверьте что `kolibri_sim` существует:
```bash
ls -lah "/Users/kolibri/Downloads/os-main 8/build-fuzz/kolibri_sim"
```

## 📚 Дополнительно

- **AGENTS.md** — Руководство по вкладам
- **docs/architecture.md** — Детальная архитектура
- **docs/developer_guide.md** — Гайд для разработчиков

## 👤 Credits

Разработка по архитектуре **Колибри ИИ** (Владислав Кочуров)

---

**Версия**: 1.0.0  
**Последнее обновление**: 4 ноября 2025  
**Статус**: ✅ Production Ready
