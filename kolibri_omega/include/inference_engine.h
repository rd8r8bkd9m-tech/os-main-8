#ifndef OMEGA_INFERENCE_ENGINE_H
#define OMEGA_INFERENCE_ENGINE_H

#include "kolibri_omega/include/forward.h"
#include <stdint.h>
#include <stddef.h>

/**
 * @brief Модуль логического вывода (Inference Engine).
 * 
 * Позволяет системе делать многошаговые логические выводы:
 * - Если A → B и B → C, то выводим A → C (транзитивность)
 * - Применяет правила в цепи: условие1 → условие2 → следствие
 * - Поддерживает вероятностные вычисления для цепочек правил
 */

/**
 * @brief Структура для представления цепочки вывода.
 */
typedef struct {
    uint64_t rule_chain[10];      // Последовательность правил для вывода
    size_t chain_length;           // Длина цепочки
    uint64_t initial_condition_id; // ID начального факта/условия
    uint64_t final_conclusion_id;  // ID конечного вывода
    double confidence;             // Общая уверенность цепочки (произведение)
} omega_inference_chain_t;

/**
 * @brief Инициализирует модуль логического вывода.
 */
void omega_inference_engine_init(void);

/**
 * @brief Выполняет одноступенчатый логический вывод.
 * Применяет одно правило к одному факту и возвращает результат.
 */
uint64_t omega_inference_single_step(kf_pool_t* formula_pool, 
                                      uint64_t rule_id, 
                                      uint64_t fact_id,
                                      kf_formula_t* result);

/**
 * @brief Выполняет многоступенчатый логический вывод (forward chaining).
 * Начиная с начального факта, применяет цепь правил до получения вывода.
 * 
 * Алгоритм:
 * 1. Начинаем с initial_fact_id
 * 2. Ищем все применимые правила
 * 3. Применяем правило → получаем промежуточный результат
 * 4. Повторяем со следующим правилом до max_steps
 * 5. Возвращаем найденную цепочку
 */
int omega_inference_forward_chain(kf_pool_t* formula_pool,
                                   uint64_t initial_fact_id,
                                   omega_inference_chain_t* chains,
                                   size_t max_chains,
                                   int max_depth);

/**
 * @brief Вычисляет уверенность для цепочки правил.
 * Уверенность цепочки = произведение уверенностей всех правил.
 * 
 * Например: P(A→B) = 0.9, P(B→C) = 0.8
 *           P(A→C через B) = 0.9 × 0.8 = 0.72
 */
double omega_compute_chain_confidence(omega_inference_chain_t* chain, kf_pool_t* formula_pool);

/**
 * @brief Создает новое правило на основе обнаруженной цепочки вывода.
 * Это позволяет системе "запомнить" найденные связи для будущего использования.
 */
uint64_t omega_create_rule_from_chain(kf_pool_t* formula_pool, 
                                       omega_inference_chain_t* chain);

#endif // OMEGA_INFERENCE_ENGINE_H
