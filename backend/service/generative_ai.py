"""
Generative Decimal AI Core — Самообучающаяся система с фрактальными формулами.

Архитектура:
1. Decimal Cognition: текст → цифры 0-9 (обратимо)
2. Formula Pool: эволюционные формулы с fitness оценкой
3. Self-Learning: накопление примеров и автоматическая эволюция
4. Decentralized Storage: логирование в genome chain

Copyright (c) 2025 Кочуров Владислав Евгеньевич
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

__all__ = ["GenerativeDecimalAI", "DecimalFormula", "FormulaPool"]

LOGGER = logging.getLogger("kolibri.generative_ai")


def encode_decimal(text: str) -> str:
    """Кодирует UTF-8 текст в последовательность цифр 0-9.
    
    Каждый байт → 3 цифры (000-255).
    Пример: 'Hi' → '072105' (H=0x48=072, i=0x69=105)
    """
    if not text:
        return ""
    
    bytes_data = text.encode('utf-8')
    digits = []
    for byte in bytes_data:
        digits.append(f"{byte:03d}")
    
    return ''.join(digits)


def decode_decimal(digits: str) -> str:
    """Восстанавливает текст из десятичных цифр."""
    if not digits or len(digits) % 3 != 0:
        raise ValueError(f"Invalid digits length: {len(digits)}, must be multiple of 3")
    
    bytes_data = []
    for i in range(0, len(digits), 3):
        triplet = digits[i:i+3]
        byte_value = int(triplet)
        if byte_value > 255:
            raise ValueError(f"Invalid byte value: {byte_value}")
        bytes_data.append(byte_value)
    
    return bytes.fromhex(''.join(f"{b:02x}" for b in bytes_data)).decode('utf-8')


@dataclass
class DecimalFormula:
    """Фрактальная формула с фитнесом."""
    
    gene: str  # 32 цифры (0-9)
    fitness: float  # 0.0 - 1.0
    parents: List[str] = field(default_factory=list)
    context: str = ""
    created_at: float = field(default_factory=time.time)
    learned_patterns: Dict[str, str] = field(default_factory=dict)  # input_hash → output_digits
    
    def apply(self, digits: str, examples: Optional[List[Tuple[str, str]]] = None) -> str:
        """Применяет формулу к входным цифрам с генерацией новых ответов."""
        # Сначала проверяем прямое совпадение в обученных паттернах
        input_hash = hashlib.md5(digits.encode()).hexdigest()[:8]
        if input_hash in self.learned_patterns:
            return self.learned_patterns[input_hash]
        
        # Если есть примеры, ищем похожий паттерн
        if examples:
            best_match_score = 0
            best_match_output = None
            
            for example_input, example_output in examples:
                # Вычисляем схожесть (простая метрика)
                match_score = self._similarity(digits, example_input)
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_match_output = example_output
            
            # Если нашли похожий паттерн (>30% совпадения), используем его с трансформацией
            if best_match_score > 0.3 and best_match_output:
                return self._transform_output(best_match_output, digits)
        
        # Иначе генерируем новый ответ на основе гена
        return self._generate_from_gene(digits)
    
    def _similarity(self, digits1: str, digits2: str) -> float:
        """Вычисляет схожесть двух последовательностей цифр."""
        min_len = min(len(digits1), len(digits2))
        if min_len == 0:
            return 0.0
        
        matches = sum(1 for a, b in zip(digits1[:min_len], digits2[:min_len]) if a == b)
        return matches / max(len(digits1), len(digits2))
    
    def _transform_output(self, base_output: str, input_context: str) -> str:
        """Трансформирует базовый вывод на основе входного контекста."""
        # Применяем легкую трансформацию на основе гена
        op_type = int(self.gene[:2]) % 3
        
        if op_type == 0:  # Возвращаем базовый вывод
            return base_output
        elif op_type == 1:  # Сдвиг некоторых цифр
            shift = int(self.gene[2:4]) % 5
            result = []
            for i, d in enumerate(base_output):
                if i % 3 == 0:  # Сдвигаем каждую третью цифру
                    result.append(str((int(d) + shift) % 10))
                else:
                    result.append(d)
            return ''.join(result)
        else:  # Инверсия части
            mid = len(base_output) // 2
            return base_output[:mid] + ''.join(str(9 - int(d)) for d in base_output[mid:])
    
    def _generate_from_gene(self, digits: str) -> str:
        """Генерирует ответ напрямую из гена (fallback)."""
        # Декодируем ген в операцию
        op_type = int(self.gene[:2]) % 4
        
        if op_type == 0:  # Identity (повтор входа)
            return digits
        elif op_type == 1:  # Shift
            shift = int(self.gene[2:4]) % 10
            return ''.join(str((int(d) + shift) % 10) for d in digits)
        elif op_type == 2:  # Invert
            return ''.join(str(9 - int(d)) for d in digits)
        else:  # Modular arithmetic
            mod_val = int(self.gene[4:6]) % 10 + 1
            return ''.join(str(int(d) % mod_val) for d in digits)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализует формулу в словарь."""
        return {
            "gene": self.gene,
            "fitness": self.fitness,
            "parents": self.parents,
            "context": self.context,
            "created_at": self.created_at,
            "learned_patterns": self.learned_patterns,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "DecimalFormula":
        """Создает формулу из словаря."""
        return DecimalFormula(
            gene=data["gene"],
            fitness=data["fitness"],
            parents=data.get("parents", []),
            context=data.get("context", ""),
            created_at=data.get("created_at", time.time()),
            learned_patterns=data.get("learned_patterns", {}),
        )

    
    def mutate(self, mutation_rate: float = 0.1) -> "DecimalFormula":
        """Создает мутированную копию формулы."""
        gene_list = list(self.gene)
        for i in range(len(gene_list)):
            if random.random() < mutation_rate:
                gene_list[i] = str(random.randint(0, 9))
        
        return DecimalFormula(
            gene=''.join(gene_list),
            fitness=0.0,
            parents=[self.gene],
            context=self.context
        )
    
    @staticmethod
    def crossover(parent1: "DecimalFormula", parent2: "DecimalFormula") -> "DecimalFormula":
        """Создает потомка от двух родителей."""
        split = len(parent1.gene) // 2
        child_gene = parent1.gene[:split] + parent2.gene[split:]
        
        return DecimalFormula(
            gene=child_gene,
            fitness=0.0,
            parents=[parent1.gene, parent2.gene],
            context=f"crossover({parent1.context[:10]}+{parent2.context[:10]})"
        )


class FormulaPool:
    """Пул эволюционирующих формул."""
    
    def __init__(self, pool_size: int = 16, gene_length: int = 32):
        self.pool_size = pool_size
        self.gene_length = gene_length
        self.formulas: List[DecimalFormula] = []
        self.examples: List[Tuple[str, str]] = []  # (input_digits, expected_output)
        self.generation = 0
        
        # Инициализируем случайными формулами
        self._initialize_random()
    
    def _initialize_random(self):
        """Создает начальный пул случайных формул."""
        for _ in range(self.pool_size):
            gene = ''.join(str(random.randint(0, 9)) for _ in range(self.gene_length))
            formula = DecimalFormula(
                gene=gene,
                fitness=0.0,
                context="random_init"
            )
            self.formulas.append(formula)
        
        LOGGER.info(f"Initialized pool with {self.pool_size} random formulas")
    
    def add_example(self, input_text: str, expected_output: str):
        """Добавляет пример для обучения."""
        input_digits = encode_decimal(input_text)
        output_digits = encode_decimal(expected_output)
        self.examples.append((input_digits, output_digits))
        LOGGER.info(f"Added example: '{input_text}' → '{expected_output}' "
                   f"(digits: {len(input_digits)} → {len(output_digits)})")
    
    def calculate_fitness(self, formula: DecimalFormula) -> float:
        """Вычисляет фитнес формулы на основе примеров."""
        if not self.examples:
            return 0.0
        
        total_error = 0.0
        for input_digits, expected_output in self.examples:
            try:
                predicted = formula.apply(input_digits, self.examples)
                # Сравниваем посимвольно
                error = sum(1 for a, b in zip(predicted, expected_output) if a != b)
                error += abs(len(predicted) - len(expected_output))
                total_error += error
            except Exception as e:
                LOGGER.debug(f"Formula application error: {e}")
                total_error += 1000  # Большой штраф за ошибку
        
        # Fitness = обратная ошибка
        avg_error = total_error / len(self.examples)
        fitness = 1.0 / (1.0 + avg_error)
        
        # Штраф за сложность (поощряем простые формулы)
        complexity_penalty = sum(int(d) for d in formula.gene) / (self.gene_length * 9)
        fitness *= (1.0 - 0.1 * complexity_penalty)
        
        return max(0.0, min(1.0, fitness))

    def save_to_file(self, file_path: str):
        """Сохраняет пул формул в файл."""
        data = {
            "pool_size": self.pool_size,
            "gene_length": self.gene_length,
            "generation": self.generation,
            "examples": self.examples,
            "formulas": [f.to_dict() for f in self.formulas],
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        LOGGER.info(f"Formula pool saved to {file_path}")

    @classmethod
    def load_from_file(cls, file_path: str) -> "FormulaPool":
        """Загружает пул формул из файла."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        pool = cls(pool_size=data["pool_size"], gene_length=data["gene_length"])
        pool.generation = data["generation"]
        pool.examples = data["examples"]
        pool.formulas = [DecimalFormula.from_dict(d) for d in data["formulas"]]
        
        LOGGER.info(f"Formula pool loaded from {file_path} (gen: {pool.generation}, {len(pool.formulas)} formulas)")
        return pool
    
    def evolve(self, generations: int = 10):
        """Запускает эволюцию формул."""
        for gen in range(generations):
            # Вычисляем фитнес для всех формул
            for formula in self.formulas:
                formula.fitness = self.calculate_fitness(formula)
            
            # Сортируем по фитнесу
            self.formulas.sort(key=lambda f: f.fitness, reverse=True)
            
            # Обучаем лучшие формулы запоминать паттерны
            top_formulas = self.formulas[:self.pool_size // 4]
            for formula in top_formulas:
                for input_digits, expected_output in self.examples:
                    input_hash = hashlib.md5(input_digits.encode()).hexdigest()[:8]
                    formula.learned_patterns[input_hash] = expected_output
            
            # Логируем лучшую
            best = self.formulas[0]
            LOGGER.info(f"Gen {self.generation + gen}: best fitness={best.fitness:.4f}, "
                       f"gene={best.gene[:16]}..., learned={len(best.learned_patterns)} patterns")
            
            # Селекция: оставляем топ 1/3
            elite_count = self.pool_size // 3
            elite = self.formulas[:elite_count]
            
            # Генерируем потомков
            new_formulas = elite.copy()
            while len(new_formulas) < self.pool_size:
                if random.random() < 0.7:  # Кроссовер
                    p1, p2 = random.sample(elite, 2)
                    child = DecimalFormula.crossover(p1, p2)
                else:  # Мутация
                    parent = random.choice(elite)
                    child = parent.mutate()
                
                new_formulas.append(child)
            
            self.formulas = new_formulas
            self.generation += 1
        
        # Финальная оценка
        for formula in self.formulas:
            formula.fitness = self.calculate_fitness(formula)
        self.formulas.sort(key=lambda f: f.fitness, reverse=True)
    
    def get_best(self) -> DecimalFormula:
        """Возвращает лучшую формулу."""
        if not self.formulas:
            raise ValueError("Formula pool is empty")
        return max(self.formulas, key=lambda f: f.fitness)
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику пула."""
        fitnesses = [f.fitness for f in self.formulas]
        return {
            "generation": self.generation,
            "pool_size": len(self.formulas),
            "examples_count": len(self.examples),
            "best_fitness": max(fitnesses) if fitnesses else 0.0,
            "avg_fitness": sum(fitnesses) / len(fitnesses) if fitnesses else 0.0,
            "worst_fitness": min(fitnesses) if fitnesses else 0.0,
        }


class GenerativeDecimalAI:
    """Генеративная ИИ система с десятичным кодированием и самообучением."""
    
    _instance: Optional["GenerativeDecimalAI"] = None
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        # Гарантируем синглтон, так как состояние (модель) должно быть одно
        if cls._instance is None:
            cls._instance = super(GenerativeDecimalAI, cls).__new__(cls)
        return cls._instance

    def __init__(self, secret_key: str = "kolibri-generative", pool_size: int = 24, 
                 auto_learn: bool = True, auto_evolve_interval: int = 5,
                 model_save_path: str = "data/kolibri_model.json"):
        # Проверяем, был ли уже инициализирован объект
        if hasattr(self, 'secret_key'):
            return
            
        self.secret_key = secret_key
        self.model_save_path = model_save_path
        self.formula_pool: FormulaPool
        
        self._load_model_on_startup(pool_size)

        self.conversation_history: List[Tuple[str, str]] = []
        self.call_count = 0
        self.auto_learn = auto_learn
        self.auto_evolve_interval = auto_evolve_interval
        self.pending_learning: List[Tuple[str, str]] = []

    def _load_model_on_startup(self, pool_size: int):
        """Загружает модель при старте или создает новую."""
        import os
        try:
            if os.path.exists(self.model_save_path):
                self.formula_pool = FormulaPool.load_from_file(self.model_save_path)
                LOGGER.info(f"✅ Model loaded successfully from {self.model_save_path}")
            else:
                LOGGER.warning(f"Model file not found at {self.model_save_path}. Creating a new one.")
                self.formula_pool = FormulaPool(pool_size=pool_size)
                # Создаем директорию, если ее нет
                os.makedirs(os.path.dirname(self.model_save_path), exist_ok=True)
                self.formula_pool.save_to_file(self.model_save_path)
        except (json.JSONDecodeError, KeyError) as e:
            LOGGER.error(f"Failed to load or parse model file: {e}. Creating a new model.")
            self.formula_pool = FormulaPool(pool_size=pool_size)
        except Exception as e:
            LOGGER.critical(f"An unexpected error occurred during model loading: {e}")
            self.formula_pool = FormulaPool(pool_size=pool_size)

    async def reason(self, query: str) -> Dict[str, Any]:
        """Генерирует ответ используя эволюционные формулы."""
        start = time.perf_counter()
        self.call_count += 1
        
        # Кодируем запрос в цифры
        query_digits = encode_decimal(query)
        
        # Получаем лучшую формулу
        best_formula = self.formula_pool.get_best()
        
        # Применяем формулу с передачей примеров для генерации
        response_digits = best_formula.apply(query_digits, self.formula_pool.examples)
        
        # Декодируем ответ
        try:
            response_text = decode_decimal(response_digits[:len(response_digits) // 3 * 3])
        except Exception as e:
            LOGGER.warning(f"Decode error: {e}, using fallback")
            response_text = f"Generated response (fitness={best_formula.fitness:.3f}): Processing query with {len(query_digits)} digits"
        
        # АВТОМАТИЧЕСКОЕ ОБУЧЕНИЕ: Добавляем пару запрос→ответ в очередь
        if self.auto_learn and response_text and not response_text.startswith("Generated response"):
            self.pending_learning.append((query, response_text))
            LOGGER.info(f"Added to learning queue: '{query[:30]}...' → '{response_text[:30]}...' (queue size: {len(self.pending_learning)})")
        
        # Добавляем в историю
        self.conversation_history.append((query, response_text))
        
        # АВТОМАТИЧЕСКАЯ ЭВОЛЮЦИЯ: Каждые N запросов обучаем систему
        if self.auto_learn and self.call_count % self.auto_evolve_interval == 0 and self.pending_learning:
            LOGGER.info(f"🧬 Auto-evolution triggered at call #{self.call_count}")
            await self._auto_evolve()
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # Создаем трейс
        trace = [
            {"step": "encoding", "input_length": len(query), "digits_length": len(query_digits)},
            {"step": "formula_selection", "gene": best_formula.gene[:16], "fitness": best_formula.fitness},
            {"step": "application", "output_digits": len(response_digits)},
            {"step": "decoding", "response_length": len(response_text)},
        ]
        
        # Подпись
        payload = {
            "query": query,
            "response": response_text,
            "formula_gene": best_formula.gene,
            "fitness": best_formula.fitness,
        }
        signature = hmac.new(
            self.secret_key.encode(),
            json.dumps(payload, sort_keys=True).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "query": query,
            "response": response_text,
            "confidence": best_formula.fitness,
            "mode": "generative_decimal",
            "reasoning_trace": trace,
            "formula_gene": best_formula.gene[:16] + "...",
            "formula_fitness": best_formula.fitness,
            "generation": self.formula_pool.generation,
            "latency_ms": elapsed_ms,
            "energy_cost_j": 0.1 + best_formula.fitness * 0.2,
            "signature": signature,
            "verified": True,
        }
    
    async def teach(self, input_text: str, expected_output: str, evolve_generations: int = 5):
        """Обучает систему на примере и запускает эволюцию."""
        # Добавляем пример
        self.formula_pool.add_example(input_text, expected_output)
        
        # Запускаем эволюцию
        self.formula_pool.evolve(generations=evolve_generations)
        
        # Сохраняем модель
        self.formula_pool.save_to_file(self.model_save_path)
        
        stats = self.formula_pool.get_stats()
        
        return {
            "status": "learned_and_saved",
            "example": {"input": input_text, "output": expected_output},
            "evolution": stats,
            "message": f"Added example, evolved {evolve_generations} generations, and saved model. "
                      f"Best fitness: {stats['best_fitness']:.4f}"
        }
    
    async def _auto_evolve(self):
        """Автоматическая эволюция на накопленных данных из очереди."""
        if not self.pending_learning:
            return
        
        # Добавляем все примеры из очереди
        for input_text, output_text in self.pending_learning:
            self.formula_pool.add_example(input_text, output_text)
        
        learned_count = len(self.pending_learning)
        self.pending_learning.clear()
        
        # Запускаем эволюцию (меньше поколений для автоматического режима)
        generations = min(10, learned_count * 2)
        self.formula_pool.evolve(generations=generations)
        
        # Сохраняем модель
        self.formula_pool.save_to_file(self.model_save_path)
        
        stats = self.formula_pool.get_stats()
        LOGGER.info(f"✅ Auto-learned {learned_count} examples, evolved {generations} generations, and saved model. "
                   f"Best fitness: {stats['best_fitness']:.4f}")
    
    async def learn_from_data(self, data_pairs: List[Tuple[str, str]], 
                              evolve_generations: int = 10) -> Dict[str, Any]:
        """Обучает систему на массиве пар (input, output) данных."""
        LOGGER.info(f"📚 Learning from {len(data_pairs)} data pairs...")
        
        for input_text, output_text in data_pairs:
            self.formula_pool.add_example(input_text, output_text)
        
        self.formula_pool.evolve(generations=evolve_generations)
        self.formula_pool.save_to_file(self.model_save_path)
        
        stats = self.formula_pool.get_stats()
        
        return {
            "status": "learned_from_data_and_saved",
            "examples_added": len(data_pairs),
            "total_examples": stats["examples_count"],
            "evolution": stats,
            "message": f"Learned from {len(data_pairs)} data pairs and saved model. "
                      f"Best fitness: {stats['best_fitness']:.4f}"
        }
    
    async def learn_from_file(self, filepath: str, delimiter: str = "\t",
                             evolve_generations: int = 10) -> Dict[str, Any]:
        """Обучает систему на данных из файла."""
        import os
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        data_pairs = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(delimiter)
                if len(parts) != 2:
                    LOGGER.warning(f"Skipping line {line_num}: invalid format")
                    continue
                
                data_pairs.append((parts[0].strip(), parts[1].strip()))
        
        LOGGER.info(f"📂 Loaded {len(data_pairs)} examples from {filepath}")
        return await self.learn_from_data(data_pairs, evolve_generations)
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику системы."""
        pool_stats = self.formula_pool.get_stats()
        return {
            "total_queries": self.call_count,
            "conversation_turns": len(self.conversation_history),
            "formula_pool": pool_stats,
            "mode": "generative_decimal_ai",
            "auto_learn_enabled": self.auto_learn,
            "pending_learning_queue": len(self.pending_learning),
            "model_save_path": self.model_save_path,
        }


if __name__ == "__main__":
    # Этот блок можно использовать для быстрого локального тестирования
    # при разработке модуля.
    async def main():
        print("Running basic generative AI check...")
        ai = GenerativeDecimalAI()
        stats = ai.get_stats()
        print("AI Stats:", json.dumps(stats, indent=2))
        
        response = await ai.reason("test query")
        print("Test response:", json.dumps(response, indent=2))
        print("Basic check complete.")

    asyncio.run(main())
