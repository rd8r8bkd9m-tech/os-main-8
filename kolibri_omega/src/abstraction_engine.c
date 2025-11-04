#include "kolibri_omega/include/abstraction_engine.h"
#include "kolibri_omega/include/types.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include "kolibri_omega/include/canvas.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

/**
 * @brief Инициализирует модуль абстракции.
 */
void omega_abstraction_engine_init(void) {
    printf("[AbstractionEngine] Initialized. Ready for knowledge abstraction and categorization.\n");
}

/**
 * @brief Категоризирует факт.
 */
uint64_t omega_categorize_fact(kf_pool_t* formula_pool, uint64_t fact_id,
                               omega_category_t* categories, size_t num_categories) {
    kf_formula_t fact;
    if (kf_get_formula(formula_pool, fact_id, &fact) != 0 || fact.type != KF_TYPE_FACT) {
        return 0;
    }
    
    // Упрощенная логика категоризации на основе значений предикатов
    for (size_t i = 0; i < num_categories; ++i) {
        omega_category_t* category = &categories[i];
        
        // Проверяем, соответствует ли факт категории
        if (category->type == CATEGORY_POSITION) {
            // Проверяем наличие position_y предиката
            for (size_t j = 0; j < fact.data.fact.num_predicates; ++j) {
                if (strcmp(fact.data.fact.predicates[j].name, "position_y") == 0) {
                    // Добавляем факт в категорию
                    if (category->member_count < MAX_FACTS_PER_CATEGORY) {
                        category->member_facts[category->member_count++] = fact_id;
                    }
                    return category->id;
                }
            }
        }
    }
    
    return 0;
}

/**
 * @brief Обнаруживает категории в текущем наборе фактов.
 */
int omega_discover_categories(omega_canvas_t* canvas, kf_pool_t* formula_pool,
                              omega_category_t* categories, size_t max_categories) {
    if (!canvas || !formula_pool || !categories || max_categories == 0) {
        return 0;
    }
    
    // Простая схема: все факты с position_y входят в категорию POSITION
    int category_count = 0;
    
    if (category_count < max_categories) {
        omega_category_t* position_category = &categories[category_count];
        position_category->id = 1;
        position_category->type = CATEGORY_POSITION;
        strcpy(position_category->name, "POSITION_FACT");
        position_category->member_count = 0;
        
        // Категоризируем все факты на холсте
        for (size_t i = 0; i < canvas->count; ++i) {
            omega_canvas_item_t* item = &canvas->items[i];
            if (item->type == OMEGA_HYPOTHESIS_FACT) {
                if (omega_categorize_fact(formula_pool, item->formula_id, categories, max_categories) > 0) {
                    // Факт был успешно категоризирован
                }
            }
        }
        
        if (position_category->member_count > 0) {
            position_category->average_confidence = 0.8;  // Высокая уверенность в прямых наблюдениях
            printf("[AbstractionEngine] Discovered category '%s' with %zu members\n",
                   position_category->name, position_category->member_count);
            category_count++;
        }
    }
    
    return category_count;
}

/**
 * @brief Создает обобщенное правило на основе категорий.
 */
uint64_t omega_create_abstract_rule(kf_pool_t* formula_pool,
                                     omega_category_t* condition_category,
                                     omega_category_t* consequence_category) {
    if (!formula_pool || !condition_category || !consequence_category) {
        return 0;
    }
    
    // Создаем "виртуальный факт" для каждой категории
    // Это плацехолдеры, которые представляют всех членов категории
    
    kf_formula_t condition_fact = {
        .type = KF_TYPE_FACT,
        .is_valid = 1,
        .time = 0,
        .data = {
            .fact = {
                .object_id = -1,  // Специальный ID для абстрактных объектов
                .num_predicates = 1
            }
        }
    };
    strcpy(condition_fact.data.fact.predicates[0].name, "category");
    strcpy(condition_fact.data.fact.predicates[0].value, condition_category->name);
    uint64_t abstract_condition_id = kf_add_formula(formula_pool, &condition_fact);
    
    kf_formula_t consequence_fact = {
        .type = KF_TYPE_FACT,
        .is_valid = 1,
        .time = 1,
        .data = {
            .fact = {
                .object_id = -1,
                .num_predicates = 1
            }
        }
    };
    strcpy(consequence_fact.data.fact.predicates[0].name, "category");
    strcpy(consequence_fact.data.fact.predicates[0].value, consequence_category->name);
    uint64_t abstract_consequence_id = kf_add_formula(formula_pool, &consequence_fact);
    
    // Создаем абстрактное правило с повышенной уверенностью (основано на категориях)
    kf_formula_t abstract_rule = {
        .type = KF_TYPE_RULE,
        .is_valid = 1,
        .time = 0,
        .data = {
            .rule = {
                .condition_formula_id = abstract_condition_id,
                .consequence_formula_id = abstract_consequence_id,
                .confidence = 0.75  // Выше, чем конкретные гипотезы (0.1)
            }
        }
    };
    
    uint64_t rule_id = kf_add_formula(formula_pool, &abstract_rule);
    
    printf("[AbstractionEngine] Created ABSTRACT RULE %llu: %s(cat:%zu) → %s(cat:%zu) (conf: 0.75)\n",
           (unsigned long long)rule_id,
           condition_category->name, condition_category->member_count,
           consequence_category->name, consequence_category->member_count);
    
    return rule_id;
}
