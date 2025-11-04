# Kolibri AI — Быстрая шпаргалка

## 🚀 Быстрый старт

```bash
# Backend
cd "/Users/kolibri/Downloads/os-main 8"
source .chatvenv/bin/activate
KOLIBRI_SSO_ENABLED=false python -m uvicorn backend.service.app:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend && npm run build
cd dist && python3 -m http.server 5173
```

**Доступ**: 
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## 📚 3 способа обучения

### 1️⃣ Автоматическое (включено по умолчанию)

Система автоматически учится на каждом запросе:

```bash
# Просто делайте запросы - система учится сама
curl -X POST http://localhost:8000/api/v1/ai/reason \
  -H "Content-Type: application/json" \
  -d '{"prompt":"hello"}'

# Каждые 5 запросов → автоэволюция
```

### 2️⃣ Загрузка массива данных

```bash
curl -X POST http://localhost:8000/api/v1/ai/learn/data \
  -H "Content-Type: application/json" \
  -d '[
    {"input": "привет", "output": "здравствуйте!"},
    {"input": "пока", "output": "до свидания!"}
  ]'
```

### 3️⃣ Загрузка из файла

**Файл** (`data/training.tsv`):
```
hello	hi there!
goodbye	see you later!
```

**Python**:
```python
from backend.service.generative_ai import GenerativeDecimalAI
import asyncio

async def load():
    ai = GenerativeDecimalAI()
    await ai.learn_from_file('data/training.tsv')

asyncio.run(load())
```

---

## 🧪 Тестирование

```bash
# Статистика
curl http://localhost:8000/api/v1/ai/generative/stats

# Запрос к AI
curl -X POST http://localhost:8000/api/v1/ai/reason \
  -H "Content-Type: application/json" \
  -d '{"prompt":"hello"}'

# Явное обучение
curl -X POST 'http://localhost:8000/api/v1/ai/teach?input_text=test&expected_output=works&evolve_generations=20'
```

---

## 📊 Ключевые метрики

| Метрика | Значение | Комментарий |
|---------|----------|-------------|
| Best fitness | 0.9948 | 99.48% точность |
| Generation | 220+ | Эволюционных поколений |
| Examples | 33+ | Обученных паттернов |
| Auto-learn | ✅ Enabled | Автообучение активно |

---

## 📂 Готовые данные

**Файл**: `data/training_examples.tsv` (33 примера)

Категории:
- Приветствия: hello, hi, good morning
- Прощания: goodbye, bye, see you
- Вопросы о системе: who are you, what can you do
- Математика: 2+2, 5*3, 10-7
- Общие: how are you, thanks, help

**Загрузить**:
```python
import asyncio, sys
sys.path.insert(0, '/Users/kolibri/Downloads/os-main 8')
from backend.service.generative_ai import GenerativeDecimalAI

async def load_dataset():
    ai = GenerativeDecimalAI()
    result = await ai.learn_from_file('data/training_examples.tsv', evolve_generations=30)
    print(f"✅ Loaded {result['examples_added']} examples, fitness={result['evolution']['best_fitness']:.4f}")

asyncio.run(load_dataset())
```

---

## 🎯 Примеры результатов

```
Query: "hello" → Response: "hi there, how can I help you?"
Query: "who are you" → Response: "I'm Kolibri AI, created by Vladislav Kochurov"
Query: "2+2" → Response: "equals 4"
Query: "привет" → Response: "здравствуйте! чем могу помочь?"
```

---

## 🔧 Настройки

```python
# Агрессивное автообучение
ai = GenerativeDecimalAI(
    auto_learn=True,
    auto_evolve_interval=2,  # Эволюция каждые 2 запроса
    pool_size=32
)

# Консервативное
ai = GenerativeDecimalAI(
    auto_learn=True,
    auto_evolve_interval=10,
    pool_size=16
)

# Только ручное
ai = GenerativeDecimalAI(
    auto_learn=False
)
```

---

## 📖 Документация

- **TEACHING_EXAMPLES.md** — Руководство по обучению через /teach
- **AUTO_LEARNING.md** — Полная документация по автообучению
- **TEST_GENERATION.md** — Проверка генерации уникальных ответов

---

## 🐛 Troubleshooting

### Система повторяет входной текст
```bash
# Проверьте фитнес
curl http://localhost:8000/api/v1/ai/generative/stats

# Если < 0.5, загрузите базовый датасет
curl -X POST http://localhost:8000/api/v1/ai/learn/data -H "Content-Type: application/json" -d @data.json
```

### Автообучение не работает
```bash
curl http://localhost:8000/api/v1/ai/generative/stats | grep auto_learn
# Должно быть: "auto_learn_enabled": true
```

### Backend не стартует
```bash
# Проверить виртуальное окружение
source .chatvenv/bin/activate

# Проверить порт
lsof -i :8000

# Логи
tail -f /tmp/backend-autolearn.log
```

---

## ⚡ Быстрые команды

```bash
# Перезапуск backend
pkill -f uvicorn; cd "/Users/kolibri/Downloads/os-main 8" && source .chatvenv/bin/activate && KOLIBRI_SSO_ENABLED=false python -m uvicorn backend.service.app:app --host 0.0.0.0 --port 8000 --reload &

# Пересборка frontend
cd "/Users/kolibri/Downloads/os-main 8/frontend" && npm run build

# Тест всех примеров
for q in "hello" "goodbye" "who are you" "2+2"; do curl -s -X POST http://localhost:8000/api/v1/ai/reason -H "Content-Type: application/json" -d "{\"prompt\":\"$q\"}" | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'{d[\"query\"]}: {d[\"response\"]}')"; done
```

---

## ✅ Чек-лист готовности

- [x] Backend на 8000 порту
- [x] Frontend на 5173 порту
- [x] Автообучение включено (auto_learn=True)
- [x] Генерация уникальных ответов (не повторяет вход)
- [x] Fitness > 0.95 (высокая точность)
- [x] Готовый датасет загружен (33 примера)
- [x] API /learn/data работает
- [x] Статистика доступна

---

**Версия**: v2.0 (с автообучением и генерацией)  
**Дата**: 4 ноября 2025 г.  
**Автор**: Кочуров Владислав Евгеньевич
