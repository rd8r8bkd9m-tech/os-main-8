#include "kolibri_omega/include/pattern_detector.h"
#include "kolibri_omega/include/types.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include <stdio.h>
#include <string.h>

/**
 * @brief Инициализирует детектор паттернов.
 */
void omega_pattern_detector_init(void) {
    printf("[PatternDetector] Initialized.\n");
}

/**
 * @brief Обнаруживает простые паттерны: последовательности из двух фактов.
 * 
 * Простая реализация, которая ищет повторяющиеся пары событий.
 */
int omega_detect_patterns(omega_canvas_t* canvas, kf_pool_t* formula_pool, omega_pattern_t* patterns, size_t max_patterns) {
    if (!canvas || !formula_pool || !patterns || max_patterns == 0) {
        return 0;
    }

    int pattern_count = 0;

    // Упрощенная логика: ищем пары фактов, которые часто происходят подряд
    for (size_t i = 0; i < canvas->count && pattern_count < max_patterns; ++i) {
        omega_canvas_item_t* item1 = &canvas->items[i];
        if (item1->type != OMEGA_HYPOTHESIS_FACT) continue;

        kf_formula_t f1;
        if (kf_get_formula(formula_pool, item1->formula_id, &f1) != 0) continue;

        for (size_t j = i + 1; j < canvas->count; ++j) {
            omega_canvas_item_t* item2 = &canvas->items[j];
            if (item2->type != OMEGA_HYPOTHESIS_FACT) continue;

            kf_formula_t f2;
            if (kf_get_formula(formula_pool, item2->formula_id, &f2) != 0) continue;

            // Если факты произошли близко друг к другу (в пределах 1 временной единицы)
            if (f2.time == f1.time + 1) {
                // Это может быть паттерн!
                omega_pattern_t* pattern = &patterns[pattern_count];
                pattern->formula_ids[0] = item1->formula_id;
                pattern->formula_ids[1] = item2->formula_id;
                pattern->length = 2;
                pattern->confidence = 50; // Средняя уверенность
                pattern->occurrences = 1;
                
                printf("[PatternDetector] Found pattern: %llu -> %llu\n",
                       (unsigned long long)item1->formula_id,
                       (unsigned long long)item2->formula_id);
                
                pattern_count++;
                if (pattern_count >= max_patterns) break;
            }
        }
    }

    return pattern_count;
}

/**
 * @brief Создает правило на основе обнаруженного паттерна.
 */
uint64_t omega_create_rule_from_pattern(kf_pool_t* formula_pool, omega_pattern_t* pattern) {
    if (!pattern || pattern->length < 2) {
        return 0;
    }

    // Создаем правило: условие (первая формула) -> следствие (последняя формула)
    kf_formula_t rule = {
        .type = KF_TYPE_RULE,
        .is_valid = 1,
        .time = 0,
        .data = {
            .rule = {
                .condition_formula_id = pattern->formula_ids[0],
                .consequence_formula_id = pattern->formula_ids[pattern->length - 1],
                .confidence = (double)pattern->confidence / 100.0
            }
        }
    };

    uint64_t rule_id = kf_add_formula(formula_pool, &rule);
    printf("[PatternDetector] Created rule %llu from detected pattern (confidence: %d%%)\n",
           (unsigned long long)rule_id, pattern->confidence);
    
    return rule_id;
}
