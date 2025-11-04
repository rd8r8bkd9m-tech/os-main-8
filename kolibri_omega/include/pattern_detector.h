#ifndef OMEGA_PATTERN_DETECTOR_H
#define OMEGA_PATTERN_DETECTOR_H

#include <stdint.h>
#include <stddef.h>
#include "kolibri_omega/include/forward.h"

/**
 * @brief Модуль обнаружения паттернов.
 * 
 * Этот модуль отвечает за обнаружение повторяющихся паттернов в истории фактов.
 * Паттерны - это последовательности событий, которые повторяются с определенной
 * вероятностью. Обнаруженные паттерны помогают AGI формировать более точные правила.
 */

typedef struct {
    uint64_t formula_ids[10];  // Последовательность формул, составляющих паттерн
    size_t length;              // Длина паттерна
    int confidence;             // Вероятность повторения паттерна (0-100)
    size_t occurrences;         // Сколько раз этот паттерн был замечен
} omega_pattern_t;

/**
 * @brief Инициализирует детектор паттернов.
 */
void omega_pattern_detector_init(void);

/**
 * @brief Обнаруживает паттерны в истории фактов на Холсте.
 * Возвращает количество найденных паттернов.
 */
int omega_detect_patterns(omega_canvas_t* canvas, kf_pool_t* formula_pool, omega_pattern_t* patterns, size_t max_patterns);

/**
 * @brief Создает правило на основе обнаруженного паттерна.
 */
uint64_t omega_create_rule_from_pattern(kf_pool_t* formula_pool, omega_pattern_t* pattern);

#endif // OMEGA_PATTERN_DETECTOR_H
