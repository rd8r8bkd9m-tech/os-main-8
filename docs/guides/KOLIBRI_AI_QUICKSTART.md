# 🚀 Kolibri AI — Быстрый старт

## ⚡ 60 секунд для начала

### Шаг 1: Активируйте окружение
```bash
cd /Users/kolibri/Downloads/os-main\ 8
source .chatvenv/bin/activate
```

### Шаг 2: Запустите сервер
```bash
uvicorn backend.service.main:app --reload
# Сервер доступен на http://localhost:8000
```

### Шаг 3: Используйте AI

**Python**:
```python
import asyncio
from backend.service.ai_core import KolibriAICore

async def main():
    ai = KolibriAICore(secret_key="test-key")
    decision = await ai.reason("What is AI?")
    print(f"Response: {decision.response}")
    print(f"Verified: {decision.verify_signature('test-key')}")

asyncio.run(main())
```

**Curl**:
```bash
curl -X POST http://localhost:8000/api/v1/ai/reason \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Что такое ИИ?"}'
```

**Python-REPL**:
```python
from backend.service.ai_core import KolibriAICore
import asyncio

ai = KolibriAICore(secret_key="dev")
result = asyncio.run(ai.reason("2+2=?"))
print(result.response)  # "The answer is 4"
```

---

## 📊 Основные API endpoints

| Метод | URL | Назначение |
|-------|-----|-----------|
| POST | `/api/v1/ai/reason` | Единичное рассуждение |
| POST | `/api/v1/ai/reason/batch` | Пакетная обработка (100 max) |
| GET | `/api/v1/ai/stats` | Статистика системы |

---

## 🧪 Запуск тестов

```bash
# Все AI тесты
pytest tests/test_ai_core.py tests/test_kolibri_api_integration.py -v

# Один тест
pytest tests/test_ai_core.py::TestKolibriAICore::test_reason_symbolic_only -v

# С покрытием
pytest --cov=backend.service.ai_core tests/test_ai_core.py
```

---

## 📚 Важные файлы

| Файл | Описание |
|------|----------|
| `backend/service/ai_core.py` | **Ядро AI (главный файл)** |
| `backend/service/routes/inference.py` | API endpoints |
| `tests/test_ai_core.py` | Unit тесты (примеры) |
| `KOLIBRI_AI_IMPLEMENTATION.md` | Полная спецификация |
| `KOLIBRI_AI_FINAL_STATUS.md` | Статус проекта |

---

## 🔧 Конфигурация

### Environment переменные

```bash
# Основные
export KOLIBRI_SECRET_KEY="my-secret"
export ENABLE_LLM="true"           # Включить локальный LLM
export LLM_ENDPOINT="http://localhost:11434"
export OFFLINE_MODE="true"         # Работать без интернета

# Производительность
export ENERGY_BUDGET="0.1"         # J (джоули)
export LATENCY_SLO="500"           # мс
```

### Python конфигурация

```python
from backend.service.ai_core import KolibriAICore, InferenceMode

ai = KolibriAICore(
    secret_key="production-key",
    enable_llm=True,              # Использовать LLM если доступен
    llm_endpoint="http://localhost:11434",
)

# Использование
decision = await ai.reason("Your query here")
print(decision.response)
print(f"Energy: {decision.energy_cost_j}J")
print(f"Verified: {decision.verify_signature('production-key')}")
```

---

## 📈 Примеры использования

### Символьное рассуждение (Fast)
```python
query = "What is 2+2?"
decision = await ai.reason(query)
# Mode: SCRIPT, Energy: 0.03J, Time: ~4ms, Confidence: 99%
```

### Гибридное рассуждение (Smart)
```python
query = "Explain photosynthesis"
decision = await ai.reason(query)
# Mode: HYBRID, Energy: 0.08J, Time: ~38ms, Confidence: 94%
```

### Пакетная обработка
```python
queries = ["Q1", "Q2", "Q3", "Q4", "Q5"]
decisions = await ai.batch_reason(queries)
# Параллельная обработка, макс 100 запросов одновременно
```

### Статистика
```python
stats = ai.get_stats()
print(f"Total queries: {stats['total_queries']}")
print(f"Total energy: {stats['total_energy_j']}J")
print(f"Avg per query: {stats['avg_energy_per_query_j']}J")
```

---

## 🔐 Верификация

```python
# Получить решение
decision = await ai.reason("query")

# Верифицировать подпись
is_valid = decision.verify_signature("my-secret-key")
if is_valid:
    print("✓ Решение подлинное")
else:
    print("✗ Решение может быть подделано")
```

---

## 🐛 Отладка

### Включить логирование
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("kolibri.ai.core")
logger.setLevel(logging.DEBUG)
```

### Проверить здоровье системы
```bash
# Статистика
curl http://localhost:8000/api/v1/ai/stats

# Тесты
pytest tests/test_ai_core.py -v

# Linting
ruff check backend/service/ai_core.py
```

### Common issues

| Проблема | Решение |
|----------|---------|
| `KolibriAICore not found` | `pip install -r requirements.txt` |
| `asyncio error` | Используйте `asyncio.run()` или `await` в async контексте |
| `Signature mismatch` | Проверьте secret_key совпадает |
| `LLM not available` | Установите ollama или отключите `enable_llm=False` |

---

## 📞 Дополнительная информация

- **Полная документация**: [`KOLIBRI_AI_IMPLEMENTATION.md`](KOLIBRI_AI_IMPLEMENTATION.md)
- **Статус проекта**: [`KOLIBRI_AI_FINAL_STATUS.md`](KOLIBRI_AI_FINAL_STATUS.md)
- **Манифест**: [`projects/kolibri_ai_edge/AGI_MANIFESTO.md`](projects/kolibri_ai_edge/AGI_MANIFESTO.md)
- **API docs**: `http://localhost:8000/docs` (Swagger UI)

---

**Готово к использованию! 🚀**
