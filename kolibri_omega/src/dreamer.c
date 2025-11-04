#include "kolibri_omega/include/types.h"
#include "kolibri_omega/include/dreamer.h"
#include "kolibri_omega/include/abstraction_engine.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include "kolibri_omega/include/canvas.h"
#include <stdio.h>
#include <string.h>

/**
 * @brief Инициализирует Сновидца.
 */
int omega_dreamer_init(omega_dreamer_t* dreamer, omega_canvas_t* canvas, kf_pool_t* formula_pool, sigma_coordinator_t* coordinator) {
    if (!dreamer || !canvas || !formula_pool || !coordinator) {
        return -1;
    }
    dreamer->canvas = canvas;
    dreamer->formula_pool = formula_pool;
    dreamer->coordinator = coordinator;
    dreamer->next_object_id = 100; // Начнем с ID 100 для создаваемых объектов
    printf("[Dreamer] Initialized.\n");
    return 0;
}

/**
 * @brief Такт Сновидца. Генерирует новые идеи, гипотезы и симуляции.
 */
void omega_dreamer_tick(omega_dreamer_t* dreamer, int current_time) {
    // Блокировки мьютексов удалены для однопоточной модели

    omega_canvas_item_t* fact1 = NULL;
    omega_canvas_item_t* fact2 = NULL;

    // PHASE 1: Конкретные гипотезы (существующий код)
    // Проходим по холсту для выбора первого факта
    for (size_t i = 0; i < dreamer->canvas->count; ++i) {
        omega_canvas_item_t* item1 = &dreamer->canvas->items[i];
        if (item1->type == OMEGA_HYPOTHESIS_FACT) {
            kf_formula_t formula1;
            if (kf_get_formula(dreamer->formula_pool, item1->formula_id, &formula1) != 0) {
                continue;
            }

            // Проходим по холсту еще раз для выбора второго факта
            for (size_t j = i + 1; j < dreamer->canvas->count; ++j) {
                omega_canvas_item_t* item2 = &dreamer->canvas->items[j];
                if (item2->type == OMEGA_HYPOTHESIS_FACT) {
                    kf_formula_t formula2;
                    if (kf_get_formula(dreamer->formula_pool, item2->formula_id, &formula2) != 0) {
                        continue;
                    }

                    // Проверяем, что факты произошли в одно время и касаются разных объектов
                    if (formula1.time == formula2.time && formula1.data.fact.object_id != formula2.data.fact.object_id) {
                        fact1 = item1;
                        fact2 = item2;
                        goto found_pair; // Нашли подходящую пару, выходим из циклов
                    }
                }
            }
        }
    }

found_pair:
    if (fact1 && fact2) {
        kf_formula_t f1, f2;
        kf_get_formula(dreamer->formula_pool, fact1->formula_id, &f1);
        kf_get_formula(dreamer->formula_pool, fact2->formula_id, &f2);

        // Создаем новую формулу-гипотезу о связи
        kf_formula_t dream_formula = {
            .type = KF_TYPE_RULE,
            .is_valid = 1, // Пока считаем гипотезу валидной
            .time = current_time,
            .data = {
                .rule = {
                    .condition_formula_id = fact1->formula_id,
                    .consequence_formula_id = fact2->formula_id,
                    .confidence = 0.1 // Начинаем с очень низкой уверенности
                }
            }
        };

        uint64_t new_formula_id = kf_add_formula(dreamer->formula_pool, &dream_formula);
        if (new_formula_id > 0) {
            // Добавляем "сон" на холст
            omega_canvas_item_t dream_item = {
                .type = OMEGA_HYPOTHESIS_DREAM,
                .formula_id = new_formula_id,
                .timestamp = current_time,
                .derived_from_rule_id = 0, // Не выведено из правила
            };
            uint64_t item_id = omega_canvas_add_item(dreamer->canvas, &dream_item);
            printf("[Dreamer] Dreamt a new rule %llu based on co-occurrence of facts %llu and %llu at time %d. New canvas item ID: %llu\n",
                   (unsigned long long)new_formula_id,
                   (unsigned long long)fact1->formula_id,
                   (unsigned long long)fact2->formula_id,
                   f1.time,
                   (unsigned long long)item_id);
        }
    }

    // PHASE 2: Обобщенные гипотезы через абстракцию (новое)
    // Обнаруживаем категории в холсте
    omega_category_t categories[10];
    memset(categories, 0, sizeof(categories));
    int num_categories = omega_discover_categories(dreamer->canvas, dreamer->formula_pool, categories, 10);
    
    if (num_categories >= 2) {
        // Создаем обобщенное правило между первой и второй категориями
        omega_create_abstract_rule(dreamer->formula_pool, &categories[0], &categories[num_categories - 1]);
    }

    // Блокировки мьютексов удалены для однопоточной модели
}

/**
 * @brief Уничтожает Сновидца, освобождая ресурсы.
 */
void omega_dreamer_destroy(omega_dreamer_t* dreamer) {
    // В текущей простой реализации здесь нечего освобождать.
    // Добавлено для полноты API.
    if (dreamer) {
        printf("[Dreamer] Destroyed.\n");
    }
}
