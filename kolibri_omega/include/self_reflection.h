#ifndef KOLIBRI_OMEGA_SELF_REFLECTION_H
#define KOLIBRI_OMEGA_SELF_REFLECTION_H

#include "kolibri_omega/include/types.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include <stdint.h>
#include <stddef.h>

/**
 * @brief Метрики качества правила для самоанализа.
 */
typedef struct {
    uint64_t rule_id;
    float confidence;
    uint32_t times_applied;
    uint32_t times_verified;
    uint32_t times_contradicted;
    float accuracy;  // times_verified / times_applied
    float quality_score;  // composite metric
    int should_delete;  // 1 if quality is too low
} omega_rule_metrics_t;

/**
 * @brief Статистика обучения системы.
 */
typedef struct {
    uint32_t total_rules;
    uint32_t high_quality_rules;  // confidence > 0.7
    uint32_t medium_quality_rules;  // 0.3 < confidence <= 0.7
    uint32_t low_quality_rules;  // confidence <= 0.3
    uint32_t rules_deleted_this_cycle;
    float average_confidence;
    float learning_speed;  // change in avg_confidence
    float prediction_accuracy;
} omega_learning_stats_t;

/**
 * @brief Инициализирует модуль самоанализа.
 */
void omega_self_reflection_init(void);

/**
 * @brief Анализирует качество отдельного правила.
 * 
 * @param formula_pool Пул формул KolibriScript
 * @param rule_id ID правила для анализа
 * @param[out] metrics Выходные метрики качества
 * @return 0 при успехе, -1 при ошибке
 */
int omega_analyze_rule_quality(kf_pool_t* formula_pool, uint64_t rule_id,
                               omega_rule_metrics_t* metrics);

/**
 * @brief Собирает статистику обучения по всем правилам.
 * 
 * @param formula_pool Пул формул KolibriScript
 * @param[out] stats Выходная статистика
 * @return Количество проанализированных правил
 */
int omega_compute_learning_stats(kf_pool_t* formula_pool,
                                 omega_learning_stats_t* stats);

/**
 * @brief Отмечает правило как примененное (increment counter).
 * 
 * @param rule_id ID правила
 */
void omega_mark_rule_applied(uint64_t rule_id);

/**
 * @brief Отмечает правило как верифицированное (prediction matched reality).
 * 
 * @param rule_id ID правила
 */
void omega_mark_rule_verified(uint64_t rule_id);

/**
 * @brief Отмечает правило как противоречивое (prediction failed).
 * 
 * @param rule_id ID правила
 */
void omega_mark_rule_contradicted(uint64_t rule_id);

/**
 * @brief Удаляет правила низкого качества.
 * 
 * @param formula_pool Пул формул
 * @param confidence_threshold Удалять правила с confidence < threshold
 * @return Количество удаленных правил
 */
int omega_cleanup_low_quality_rules(kf_pool_t* formula_pool,
                                    float confidence_threshold);

/**
 * @brief Выполняет полный самоанализ системы.
 * 
 * Включает:
 * - Расчет метрик для всех правил
 * - Сбор статистики обучения
 * - Удаление низко-качественных правил
 * - Вывод логов с результатами
 * 
 * @param formula_pool Пул формул
 */
void omega_full_self_reflection(kf_pool_t* formula_pool);

#endif  // KOLIBRI_OMEGA_SELF_REFLECTION_H
