#include "kolibri_omega/include/types.h"
#include "kolibri_omega/include/observer.h"
#include "kolibri_omega/include/learning_engine.h"
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include "../include/canvas.h"
#include "../stubs/sigma_coordinator_stub.h"
#include "../stubs/kf_pool_stub.h"

/**
 * @brief Инициализирует Наблюдателя.
 */
int omega_observer_init(omega_observer_t* observer, omega_canvas_t* canvas, sigma_coordinator_t* coordinator) {
    if (!observer || !canvas || !coordinator) return -1;
    observer->canvas = canvas;
    observer->coordinator = coordinator;
    return 0;
}

/**
 * @brief Уничтожает Наблюдателя, освобождая все ресурсы.
 */
void omega_observer_destroy(omega_observer_t* observer) {
    // В этой реализации нет динамической памяти для уничтожения
}

/**
 * @brief Основной цикл работы Наблюдателя.
 *
 * Сканирует холст на наличие противоречий и сообщает о них координатору.
 */
void omega_observer_tick(omega_observer_t* observer) {
    // pthread_mutex_lock(&observer->canvas->mutex); // УДАЛЕНО: не нужно в однопоточном режиме

    // --- Фаза 1: Проверка ПРЕДСКАЗАНИЙ ---
    for (size_t i = 0; i < observer->canvas->count; ) {
        omega_canvas_item_t* prediction_item = &observer->canvas->items[i];

        if (prediction_item->type != OMEGA_HYPOTHESIS_PREDICTION) {
            i++;
            continue;
        }

        kf_formula_t prediction_formula;
        if (kf_get_formula(observer->canvas->formula_pool, prediction_item->formula_id, &prediction_formula) == 0) {
            // Ищем соответствующий факт
            for (size_t j = 0; j < observer->canvas->count; ++j) {
                omega_canvas_item_t* fact_item = &observer->canvas->items[j];
                if (fact_item->type != OMEGA_HYPOTHESIS_FACT) continue;

                kf_formula_t fact_formula;
                if (kf_get_formula(observer->canvas->formula_pool, fact_item->formula_id, &fact_formula) != 0) continue;

                // Сравниваем факт и предсказание
                if (fact_formula.time == prediction_formula.time && fact_formula.data.fact.object_id == prediction_formula.data.fact.object_id) {
                    if (kf_are_contradictory(observer->canvas->formula_pool, fact_item->formula_id, prediction_item->formula_id)) {
                        printf("[Observer] Contradiction found between fact %llu and prediction %llu!\n",
                               (unsigned long long)fact_item->formula_id,
                               (unsigned long long)prediction_item->formula_id);
                        
                        // Обновляем уверенность правила, на основе которого было создано неверное предсказание
                        if (prediction_item->derived_from_rule_id > 0) {
                            omega_update_rule_confidence(observer->canvas->formula_pool, 
                                                        prediction_item->derived_from_rule_id, 
                                                        0);  // 0 = неверное предсказание
                        }
                        
                        sigma_task_t task = {
                            .type = TASK_INVALID_RULE,
                            .data = { .invalid_rule = { .rule_id = prediction_item->derived_from_rule_id } }
                        };
                        sigma_add_task(observer->coordinator, &task);
                        omega_canvas_remove_item(observer->canvas, i);
                        return; // Выходим после нахождения и обработки противоречия
                    }
                    break; 
                }
            }
        }
        i++;
    }

    // --- Фаза 2: Поиск прямых противоречий между ФАКТАМИ ---
    for (size_t i = 0; i < observer->canvas->count; ++i) {
        for (size_t j = i + 1; j < observer->canvas->count; ++j) {
            omega_canvas_item_t* item1 = &observer->canvas->items[i];
            omega_canvas_item_t* item2 = &observer->canvas->items[j];

            if (item1->type == OMEGA_HYPOTHESIS_FACT && item2->type == OMEGA_HYPOTHESIS_FACT) {
                if (kf_are_contradictory(observer->canvas->formula_pool, item1->formula_id, item2->formula_id)) {
                    printf("[Observer] Found contradiction between fact %llu and fact %llu.\n", (unsigned long long)item1->formula_id, (unsigned long long)item2->formula_id);
                    sigma_task_t task = {
                        .type = TASK_CONTRADICTION,
                        .data = { .contradiction = {item1->formula_id, item2->formula_id} }
                    };
                    sigma_add_task(observer->coordinator, &task);
                    return; // Выходим после нахождения и обработки противоречия
                }
            }
        }
    }
}
