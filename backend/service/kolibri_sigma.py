"""
Kolibri-Sigma Core — Коллективное сознание на базе специализированных модулей.

Архитектура:
1.  **Лобы (Lobes):** Специализированные пулы формул (синтаксис, логика, семантика).
2.  **Координатор (Coordinator):** Легковесный маршрутизатор, который декомпозирует
    запросы и синтезирует ответы из "мнений" разных лобов.
3.  **Геном Сознания:** Карта связей между лобами, фиксирующая успешные
    мыслительные паттерны.

Copyright (c) 2025 Кочуров Владислав Евгеньевич
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable

# --- Базовые компоненты, перенесенные из generative_ai.py ---

LOGGER = logging.getLogger("kolibri.sigma")

def encode_decimal(text: str) -> str:
    if not text:
        return ""
    return ''.join(f"{byte:03d}" for byte in text.encode('utf-8'))

def decode_decimal(digits: str) -> str:
    """Восстанавливает текст из десятичных цифр, мягко обрабатывая некорректные значения."""
    if not digits:
        return ""
    
    # Выравниваем длину до кратной 3
    valid_len = len(digits) // 3 * 3
    if valid_len == 0:
        return ""
        
    bytes_data = []
    for i in range(0, valid_len, 3):
        triplet = digits[i:i+3]
        byte_value = int(triplet)
        # Приводим значение к допустимому диапазону [0, 255] вместо падения
        clamped_byte = min(byte_value, 255)
        bytes_data.append(clamped_byte)
    
    return bytes(bytes_data).decode('utf-8', errors='ignore')

@dataclass
class DecimalFormula:
    gene: str
    fitness: float = 0.0
    parents: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def apply(self, digits: str) -> str:
        op_type = int(self.gene[:2]) % 4
        if op_type == 0:
            return digits
        elif op_type == 1:
            shift = int(self.gene[2:4]) % 10
            return ''.join(str((int(d) + shift) % 10) for d in digits)
        elif op_type == 2:
            return ''.join(str(9 - int(d)) for d in digits)
        else:
            mod_val = int(self.gene[4:6]) % 10 + 1
            return ''.join(str(int(d) % mod_val) for d in digits)

    def mutate(self, mutation_rate: float = 0.1) -> "DecimalFormula":
        gene_list = list(self.gene)
        for i in range(len(gene_list)):
            if random.random() < mutation_rate:
                gene_list[i] = str(random.randint(0, 9))
        return DecimalFormula(gene=''.join(gene_list), parents=[self.gene])

    @staticmethod
    def crossover(p1: "DecimalFormula", p2: "DecimalFormula") -> "DecimalFormula":
        split = len(p1.gene) // 2
        child_gene = p1.gene[:split] + p2.gene[split:]
        return DecimalFormula(gene=child_gene, parents=[p1.gene, p2.gene])

# --- Новая архитектура "Колибри-Сигма" ---

class BaseLobe:
    """Базовый класс для специализированного пула формул (Лоба)."""
    
    def __init__(self, name: str, pool_size: int = 16, gene_length: int = 32):
        self.name = name
        self.pool_size = pool_size
        self.gene_length = gene_length
        self.formulas: List[DecimalFormula] = self._initialize_random()
        self.examples: List[Tuple[str, str]] = []
        self.generation = 0

    def _initialize_random(self) -> List[DecimalFormula]:
        return [
            DecimalFormula(
                gene=''.join(str(random.randint(0, 9)) for _ in range(self.gene_length))
            ) for _ in range(self.pool_size)
        ]

    def add_example(self, input_text: str, expected_output: str):
        self.examples.append((input_text, expected_output))

    def get_fitness_calculator(self) -> Callable[[DecimalFormula, List[Tuple[str, str]]], float]:
        """Возвращает функцию для расчета фитнеса. Должна быть переопределена."""
        raise NotImplementedError("Каждый Лоб должен иметь свою фитнес-функцию.")

    def evolve(self, generations: int = 1):
        if not self.examples:
            return

        fitness_calculator = self.get_fitness_calculator()

        for _ in range(generations):
            for formula in self.formulas:
                formula.fitness = fitness_calculator(formula, self.examples)
            
            self.formulas.sort(key=lambda f: f.fitness, reverse=True)
            
            elite_count = self.pool_size // 3
            elite = self.formulas[:elite_count]
            
            if not elite: return

            new_formulas = elite.copy()
            while len(new_formulas) < self.pool_size:
                if random.random() < 0.7:
                    p1, p2 = random.sample(elite, 2)
                    child = DecimalFormula.crossover(p1, p2)
                else:
                    parent = random.choice(elite)
                    child = parent.mutate()
                new_formulas.append(child)
            
            self.formulas = new_formulas
            self.generation += 1
        
        LOGGER.info(f"Лоб '{self.name}' эволюционировал. Поколение: {self.generation}, "
                    f"Лучший фитнес: {self.get_best().fitness:.4f}")

    def get_best(self) -> DecimalFormula:
        if not self.formulas:
            raise ValueError(f"Лоб '{self.name}' пуст.")
        return max(self.formulas, key=lambda f: f.fitness)

    def get_opinion(self, query: str) -> str:
        """Возвращает "мнение" Лоба на запрос."""
        query_digits = encode_decimal(query)
        best_formula = self.get_best()
        opinion_digits = best_formula.apply(query_digits)
        try:
            return decode_decimal(opinion_digits)
        except ValueError:
            return "" # Возвращаем пустую строку в случае ошибки декодирования

class LogicLobe(BaseLobe):
    """Лоб, отвечающий за математику и логику."""
    def get_fitness_calculator(self) -> Callable[[DecimalFormula, List[Tuple[str, str]]], float]:
        def calculate(formula: DecimalFormula, examples: List[Tuple[str, str]]) -> float:
            score = 0
            for input_text, expected_output in examples:
                # Ищем простые арифм. выражения: "2+2", "5*3"
                match = re.match(r"(\d+)\s*([+\-*/])\s*(\d+)", input_text)
                if match:
                    try:
                        # Ожидаемый результат
                        expected_result = str(eval(input_text))
                        # Результат от формулы
                        predicted_text = decode_decimal(formula.apply(encode_decimal(input_text)))
                        
                        if expected_result in predicted_text:
                            score += 1
                    except:
                        continue
            return score / (len(examples) + 1e-6)
        return calculate

class SyntaxLobe(BaseLobe):
    """Лоб, отвечающий за грамматическую структуру."""
    def get_fitness_calculator(self) -> Callable[[DecimalFormula, List[Tuple[str, str]]], float]:
        def calculate(formula: DecimalFormula, examples: List[Tuple[str, str]]) -> float:
            score = 0
            for input_text, expected_output in examples:
                predicted_text = decode_decimal(formula.apply(encode_decimal(input_text)))
                # Простейшая проверка: осмысленный ответ должен содержать пробелы
                if ' ' in predicted_text and len(predicted_text) > 3:
                    score += 1
            return score / (len(examples) + 1e-6)
        return calculate

class SemanticLobe(BaseLobe):
    """Лоб, отвечающий за ассоциации и смысл."""
    def get_fitness_calculator(self) -> Callable[[DecimalFormula, List[Tuple[str, str]]], float]:
        def calculate(formula: DecimalFormula, examples: List[Tuple[str, str]]) -> float:
            score = 0
            for input_text, expected_output in examples:
                predicted_text = decode_decimal(formula.apply(encode_decimal(input_text)))
                # Простая проверка: есть ли в ответе слова из ожидаемого вывода
                expected_words = set(expected_output.lower().split())
                predicted_words = set(predicted_text.lower().split())
                if expected_words & predicted_words:
                    score += 1
            return score / (len(examples) + 1e-6)
        return calculate

class SigmaCoordinator:
    """Координатор, управляющий Лобами и синтезирующий ответы."""
    
    def __init__(self):
        self.lobes: Dict[str, BaseLobe] = {
            "logic": LogicLobe("logic"),
            "syntax": SyntaxLobe("syntax"),
            "semantic": SemanticLobe("semantic"),
        }
        self.meta_formula: DecimalFormula = DecimalFormula(
            gene=''.join(str(random.randint(0, 9)) for _ in range(32))
        )
        LOGGER.info("Координатор 'Колибри-Сигма' инициализирован.")

    def teach(self, input_text: str, expected_output: str):
        """Обучает все Лобы на одном примере."""
        LOGGER.info(f"Обучение на примере: '{input_text}' -> '{expected_output}'")
        for lobe in self.lobes.values():
            lobe.add_example(input_text, expected_output)
            lobe.evolve()
    
    def reason(self, query: str) -> Dict[str, Any]:
        """Формирует ответ, опрашивая Лобы и синтезируя их мнения."""
        start_time = time.perf_counter()
        
        opinions: Dict[str, str] = {}
        for name, lobe in self.lobes.items():
            opinions[name] = lobe.get_opinion(query)

        # Синтез ответа: простая конкатенация для прототипа
        # В будущем здесь будет применяться мета-формула
        logic_opinion = opinions.get("logic", "")
        semantic_opinion = opinions.get("semantic", "")
        syntax_opinion = opinions.get("syntax", "")

        # Приоритет для логического ответа, если он есть
        if logic_opinion and logic_opinion.isdigit():
            final_response = f"Результат вычислений: {logic_opinion}"
        elif semantic_opinion:
            final_response = semantic_opinion
        else:
            final_response = syntax_opinion

        latency = (time.perf_counter() - start_time) * 1000

        return {
            "query": query,
            "response": final_response,
            "reasoning_trace": {
                "opinions": opinions,
                "synthesis_strategy": "logic_priority"
            },
            "latency_ms": latency,
        }

# --- Тестовый блок для демонстрации ---
async def test_kolibri_sigma():
    """Тестирование архитектуры 'Колибри-Сигма'."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("\n" + "="*70)
    print("🐦 KOLIBRI-SIGMA: COLLECTIVE CONSCIOUSNESS TEST")
    print("="*70 + "\n")

    sigma = SigmaCoordinator()

    # Обучение
    print("--- 📚 Обучение ---")
    sigma.teach("сколько будет 5 * 10", "50")
    sigma.teach("столица России", "Москва")
    sigma.teach("какого цвета небо", "голубое")
    print("\n--- ✅ Обучение завершено ---\n")

    # Тестирование
    print("--- 🧪 Тестирование ---")
    
    # 1. Тест на логику
    query1 = "5 * 10"
    result1 = sigma.reason(query1)
    print(f"Q: {query1}")
    print(f"A: {result1['response']}")
    print(f"   (Мнения: {result1['reasoning_trace']['opinions']})\n")

    # 2. Тест на семантику
    query2 = "столица России"
    result2 = sigma.reason(query2)
    print(f"Q: {query2}")
    print(f"A: {result2['response']}")
    print(f"   (Мнения: {result2['reasoning_trace']['opinions']})\n")

    # 3. Тест на генерацию
    query3 = "придумай что-нибудь"
    result3 = sigma.reason(query3)
    print(f"Q: {query3}")
    print(f"A: {result3['response']}")
    print(f"   (Мнения: {result3['reasoning_trace']['opinions']})\n")

    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_kolibri_sigma())
