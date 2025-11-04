# Автоматическое обучение на входных данных

## ✅ Реализовано

Система **Kolibri AI** теперь автоматически обучается на всех входящих запросах и данных!

### 3 способа обучения

#### 1. Автоматическое обучение на запросах (Auto-Learning)

Система автоматически запоминает каждый запрос→ответ и эволюционирует каждые N запросов:

```python
# По умолчанию включено
ai = GenerativeDecimalAI(
    auto_learn=True,           # Автоматическое обучение
    auto_evolve_interval=5     # Эволюция каждые 5 запросов
)

# Делаем запросы - система учится автоматически
await ai.reason("hello")       # Добавлено в очередь
await ai.reason("goodbye")     # Добавлено в очередь
await ai.reason("thanks")      # Добавлено в очередь
await ai.reason("hi")          # Добавлено в очередь
await ai.reason("bye")         # 5-й запрос → АВТОЭВОЛЮЦИЯ!
# Система автоматически обучилась на 5 примерах
```

**Как работает**:
- Каждый запрос с успешным ответом добавляется в `pending_learning` очередь
- Каждые `auto_evolve_interval` запросов система:
  1. Берёт все примеры из очереди
  2. Добавляет их в пул примеров
  3. Запускает эволюцию (min(10, learned_count * 2) поколений)
  4. Очищает очередь

#### 2. Загрузка массива данных через API

```bash
# Загрузить JSON массив пар input→output
curl -X POST http://localhost:8000/api/v1/ai/learn/data \
  -H "Content-Type: application/json" \
  -d '[
    {"input": "hello", "output": "hi there, how can I help?"},
    {"input": "goodbye", "output": "see you later!"},
    {"input": "thanks", "output": "you are welcome!"}
  ]'

# Ответ:
{
  "status": "learned_from_data",
  "examples_added": 3,
  "total_examples": 15,
  "evolution": {
    "generation": 40,
    "best_fitness": 0.9823
  }
}
```

**Параметры**:
- `evolve_generations` (опционально, 1-100, по умолчанию 10)
- Максимум 1000 примеров за раз

#### 3. Загрузка из файла

**Формат файла** (`training_examples.tsv`):
```
# Комментарии начинаются с #
input_text<TAB>output_text

hello	hi there
goodbye	see you later
thanks	you're welcome
```

**Через Python API**:
```python
result = await ai.learn_from_file(
    filepath='data/training_examples.tsv',
    delimiter='\t',
    evolve_generations=30
)
print(f"Loaded {result['examples_added']} examples")
print(f"Best fitness: {result['evolution']['best_fitness']:.4f}")
```

**Готовый файл**: `/data/training_examples.tsv` (33 примера)

## Примеры использования

### Пример 1: Обучение на диалогах

```python
from backend.service.generative_ai import GenerativeDecimalAI
import asyncio

async def learn_from_conversations():
    ai = GenerativeDecimalAI(auto_learn=True, auto_evolve_interval=3)
    
    # Загружаем базовые знания
    await ai.learn_from_data([
        ("hello", "hi! how can I help?"),
        ("help", "I'm here to assist you"),
    ], evolve_generations=10)
    
    # Делаем запросы - система автоматически учится
    response1 = await ai.reason("hello")
    response2 = await ai.reason("help")
    response3 = await ai.reason("hello")  # 3-й запрос → автоэволюция!
    
    # Проверяем статистику
    stats = ai.get_stats()
    print(f"Examples learned: {stats['formula_pool']['examples_count']}")
    print(f"Auto-learn queue: {stats['pending_learning_queue']}")

asyncio.run(learn_from_conversations())
```

### Пример 2: Массовая загрузка данных

```bash
# Подготовить JSON файл
cat > training_data.json << 'EOF'
[
  {"input": "what is AI", "output": "artificial intelligence: systems that learn"},
  {"input": "explain ML", "output": "machine learning: algorithms that improve through experience"},
  {"input": "neural network", "output": "computational model inspired by brain"},
  {"input": "deep learning", "output": "ML using multi-layer neural networks"}
]
EOF

# Загрузить через API
curl -X POST http://localhost:8000/api/v1/ai/learn/data \
  -H "Content-Type: application/json" \
  -d @training_data.json

# Проверить результат
curl http://localhost:8000/api/v1/ai/generative/stats
```

### Пример 3: Создание обучающего датасета

```python
# create_dataset.py
import asyncio
from backend.service.generative_ai import GenerativeDecimalAI

async def create_qa_dataset():
    """Создаёт датасет вопрос-ответ для конкретной предметной области."""
    
    # FAQ для техподдержки
    tech_support_qa = [
        ("how to reset password", "go to settings → security → reset password"),
        ("forgot username", "click 'forgot username' on login page"),
        ("account locked", "contact support at support@kolibri.ai"),
        ("error 404", "the page you requested was not found"),
        ("slow performance", "clear cache and restart the application"),
        ("backup data", "go to settings → backup → export data"),
        ("delete account", "settings → account → delete account (irreversible)"),
    ]
    
    ai = GenerativeDecimalAI(pool_size=32, auto_learn=False)
    
    # Загружаем весь датасет сразу
    result = await ai.learn_from_data(tech_support_qa, evolve_generations=40)
    
    print(f"✅ Loaded {result['examples_added']} tech support examples")
    print(f"   Fitness: {result['evolution']['best_fitness']:.4f}")
    
    # Тестируем
    test_queries = ["reset password", "account locked", "error 404"]
    for query in test_queries:
        response = await ai.reason(query)
        print(f"\nQ: {query}")
        print(f"A: {response['response']}")

asyncio.run(create_qa_dataset())
```

## Архитектура автообучения

```
┌─────────────────────────────────────────────────────────────┐
│                     Входящий запрос                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  reason(query) │
              └────────┬───────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
  ┌──────────────┐          ┌──────────────────┐
  │ Генерация    │          │ Auto-Learning    │
  │ ответа       │          │ (если включено)  │
  └──────┬───────┘          └────────┬─────────┘
         │                           │
         │                           ▼
         │                  ┌─────────────────┐
         │                  │ pending_learning│
         │                  │ queue.append()  │
         │                  └────────┬────────┘
         │                           │
         │                           ▼
         │              ┌────────────────────────┐
         │              │ call_count %           │
         │              │ auto_evolve_interval?  │
         │              └─────────┬──────────────┘
         │                        │
         │                 Да ◄───┤
         │                        │
         │                        ▼
         │              ┌─────────────────┐
         │              │ _auto_evolve()  │
         │              ├─────────────────┤
         │              │ 1. add_example()│
         │              │ 2. evolve(N)    │
         │              │ 3. clear queue  │
         │              └─────────────────┘
         │
         └──────────────► Возврат ответа
```

## Статистика системы

```bash
curl http://localhost:8000/api/v1/ai/generative/stats | python3 -m json.tool
```

**Новые поля**:
```json
{
  "total_queries": 47,
  "formula_pool": {
    "generation": 120,
    "examples_count": 37,
    "best_fitness": 0.9854
  },
  "auto_learn_enabled": true,        ← Автообучение включено
  "pending_learning_queue": 2         ← 2 примера в очереди
}
```

## Настройки автообучения

```python
# Агрессивное обучение (каждые 2 запроса)
ai = GenerativeDecimalAI(
    auto_learn=True,
    auto_evolve_interval=2,
    pool_size=32
)

# Консервативное обучение (каждые 10 запросов)
ai = GenerativeDecimalAI(
    auto_learn=True,
    auto_evolve_interval=10,
    pool_size=16
)

# Только ручное обучение
ai = GenerativeDecimalAI(
    auto_learn=False  # Отключить автообучение
)
```

## Рекомендации

### Для продакшена
- `auto_learn=True` — включайте автообучение
- `auto_evolve_interval=5-10` — баланс между обучением и производительностью
- `pool_size=24-32` — достаточно для хорошей эволюции
- Периодически сохраняйте модель

### Для обучения
- Используйте `learn_from_data()` для массовой загрузки
- Начните с 50-100 качественных примеров
- `evolve_generations=30-50` для начального обучения
- Затем включайте `auto_learn` для дообучения

### Для тестирования
- `auto_learn=False` — контролируемые тесты
- Загружайте тестовые данные через `learn_from_file()`
- Замеряйте фитнес до и после обучения

## Производительность

| Операция | Время | Примечание |
|----------|-------|------------|
| `reason()` без авто-эволюции | ~3-5 мс | Быстрый ответ |
| `reason()` с авто-эволюцией | ~50-100 мс | Каждые N запросов |
| `learn_from_data(100)` | ~200-300 мс | Единоразовая загрузка |
| `learn_from_file(50 примеров)` | ~150-200 мс | Чтение файла + обучение |

## Troubleshooting

### Автообучение не работает
```python
stats = ai.get_stats()
print(f"Auto-learn: {stats['auto_learn_enabled']}")  # Должно быть True
print(f"Queue: {stats['pending_learning_queue']}")   # Растёт с запросами
```

### Низкий фитнес после автообучения
- Увеличьте `auto_evolve_interval` (больше примеров → лучше эволюция)
- Проверьте качество примеров в очереди
- Загрузите базовый датасет через `learn_from_data()`

### Файл не загружается
```python
import os
print(os.path.exists('/path/to/file.tsv'))  # Проверить путь
```

Убедитесь, что:
- Файл использует правильный разделитель (по умолчанию `\t`)
- Каждая строка: `input<delimiter>output`
- UTF-8 кодировка
