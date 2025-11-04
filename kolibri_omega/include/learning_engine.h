#ifndef OMEGA_LEARNING_ENGINE_H
#define OMEGA_LEARNING_ENGINE_H

#include "kolibri_omega/include/forward.h"
#include <stdint.h>

/**
 * @brief Модуль обучения системы.
 * 
 * Отвечает за адаптивное изменение уверенности правил на основе:
 * - Количества верных предсказаний
 * - Количества неверных предсказаний (противоречий)
 * - Истории применения правила
 */

/**
 * @brief Обновляет уверенность правила на основе его точности.
 * 
 * Если предсказание, сделанное на основе правила, совпадает с фактом:
 *   confidence_new = confidence_old * 0.9 + 0.1 * 1.0  (улучшение)
 * 
 * Если найдено противоречие:
 *   confidence_new = confidence_old * 0.8 + 0.1 * 0.0  (снижение)
 */
void omega_update_rule_confidence(kf_pool_t* formula_pool, uint64_t rule_id, int was_correct);

/**
 * @brief Вычисляет общую точность правила на основе количества успешных/неудачных применений.
 * Возвращает значение от 0.0 до 1.0.
 */
double omega_calculate_rule_accuracy(kf_pool_t* formula_pool, uint64_t rule_id);

/**
 * @brief Ранжирует все правила по уверенности.
 * Это используется предсказателем для выбора наиболее надежных правил в первую очередь.
 */
void omega_rank_rules_by_confidence(kf_pool_t* formula_pool);

#endif // OMEGA_LEARNING_ENGINE_H
