#include "kolibri_omega/include/types.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void kf_pool_init(kf_pool_t* pool) {
    pool->count = 0;
    pool->next_id = 1000;
    // pthread_mutex_init(&pool->mutex, NULL); // Удалено
}

void kf_pool_destroy(kf_pool_t* pool) {
    // pthread_mutex_destroy(&pool->mutex); // Удалено
}

uint64_t kf_add_formula(kf_pool_t* pool, kf_formula_t* formula) {
    if (pool->count >= MAX_FORMULAS) {
        return 0;
    }
    formula->id = pool->next_id++;
    formula->is_valid = 1; // По умолчанию все валидно
    pool->formulas[pool->count++] = *formula;
    return formula->id;
}

int kf_get_formula(kf_pool_t* pool, uint64_t formula_id, kf_formula_t* formula) {
    for (size_t i = 0; i < pool->count; ++i) {
        if (pool->formulas[i].id == formula_id) {
            *formula = pool->formulas[i];
            return 0;
        }
    }
    return -1;
}

int kf_set_formula(kf_pool_t* pool, uint64_t formula_id, kf_formula_t* formula) {
    for (size_t i = 0; i < pool->count; ++i) {
        if (pool->formulas[i].id == formula_id) {
            pool->formulas[i] = *formula;
            return 0;
        }
    }
    return -1;
}

// Упрощенная проверка на противоречие: две формулы противоречат, если у них один и тот же объект в одно и то же время, но разные предикаты.
int kf_are_contradictory(kf_pool_t* pool, uint64_t formula_id1, uint64_t formula_id2) {
    kf_formula_t f1, f2;
    if (kf_get_formula(pool, formula_id1, &f1) != 0 || kf_get_formula(pool, formula_id2, &f2) != 0) {
        return 0; // Не удалось получить формулы
    }

    if (f1.type != KF_TYPE_FACT || f2.type != KF_TYPE_FACT) {
        return 0; // Сравниваем только факты
    }

    if (f1.data.fact.object_id == f2.data.fact.object_id && f1.time == f2.time) {
        if (f1.data.fact.num_predicates != f2.data.fact.num_predicates) return 1; // Разное количество предикатов - уже противоречие
        for(size_t i=0; i < f1.data.fact.num_predicates; ++i) {
            if (strcmp(f1.data.fact.predicates[i].name, f2.data.fact.predicates[i].name) != 0 || strcmp(f1.data.fact.predicates[i].value, f2.data.fact.predicates[i].value) != 0) {
                return 1; // Найден предикат с тем же именем, но разным значением
            }
        }
    }
    return 0;
}

uint64_t kf_create_rule_from_facts(kf_pool_t* pool, uint64_t fact_id1, uint64_t fact_id2) {
    kf_formula_t rule = {
        .type = KF_TYPE_RULE,
        .is_valid = 1,
        .time = 0, // Время создания правила, можно уточнить
        .data = {
            .rule = {
                .condition_formula_id = fact_id1,
                .consequence_formula_id = fact_id2,
                .confidence = 0.5 // Начальная уверенность
            }
        }
    };
    return kf_add_formula(pool, &rule);
}

int kf_apply_rule_to_fact(kf_pool_t* pool, uint64_t rule_id, uint64_t fact_id, kf_formula_t* predicted_formula) {
    // Заглушка: создает фиктивное предсказание
    kf_formula_t fact;
    if (kf_get_formula(pool, fact_id, &fact) != 0) return -1;

    // Простое правило: предсказываем, что свойство объекта изменится так же, как в правиле
    *predicted_formula = (kf_formula_t){
        .type = KF_TYPE_FACT,
        .is_valid = 1,
        .time = fact.time + 1, // Предсказываем на следующий такт
        .data.fact.object_id = fact.data.fact.object_id,
        .data.fact.num_predicates = 1
    };
    strcpy(predicted_formula->data.fact.predicates[0].name, "predicted_state");
    snprintf(predicted_formula->data.fact.predicates[0].value, sizeof(predicted_formula->data.fact.predicates[0].value), "from_rule_%llu", (unsigned long long)rule_id);

    return 0;
}

/**
 * @brief Создает новое правило, объясняющее противоречие.
 * Это правило может использоваться для разрешения противоречий в будущих наблюдениях.
 */
uint64_t kf_create_rule_for_contradiction(kf_pool_t* pool, uint64_t contradicting_fact_id1, uint64_t contradicting_fact_id2) {
    kf_formula_t fact1, fact2;
    if (kf_get_formula(pool, contradicting_fact_id1, &fact1) != 0 || kf_get_formula(pool, contradicting_fact_id2, &fact2) != 0) {
        return 0; // Не удалось получить факты
    }

    // Создаем правило: если произойдет ситуация как в fact1, то будет состояние как в fact2
    // Это правило помогает AGI учиться объяснять противоречия через причинно-следственные связи
    kf_formula_t explanation_rule = {
        .type = KF_TYPE_RULE,
        .is_valid = 1,
        .time = fact2.time,
        .data = {
            .rule = {
                .condition_formula_id = contradicting_fact_id1,
                .consequence_formula_id = contradicting_fact_id2,
                .confidence = 0.1  // Низкая уверенность, так как мы просто объясняем противоречие
            }
        }
    };
    
    uint64_t rule_id = kf_add_formula(pool, &explanation_rule);
    printf("[KF Pool] Created explanation rule %llu to resolve contradiction between %llu and %llu\n",
           (unsigned long long)rule_id, (unsigned long long)contradicting_fact_id1, (unsigned long long)contradicting_fact_id2);
    return rule_id;
}

void kf_print_formula(kf_pool_t* pool, uint64_t formula_id) {
    kf_formula_t f;
    if (kf_get_formula(pool, formula_id, &f) == 0) {
        printf("Formula %llu (Type: %s, Valid: %d, Time: %d): ",
               (unsigned long long)f.id, f.type == KF_TYPE_FACT ? "FACT" : "RULE", f.is_valid, f.time);
        if (f.type == KF_TYPE_FACT) {
            printf("ObjID: %d, ", f.data.fact.object_id);
            for (size_t i = 0; i < f.data.fact.num_predicates; ++i) {
                printf("%s=%s; ", f.data.fact.predicates[i].name, f.data.fact.predicates[i].value);
            }
        } else {
            printf("Rule: %llu -> %llu, Conf: %.2f", 
                   (unsigned long long)f.data.rule.condition_formula_id, 
                   (unsigned long long)f.data.rule.consequence_formula_id,
                   f.data.rule.confidence);
        }
        printf("\n");
    }
}

int kf_invalidate_rule(kf_pool_t* pool, uint64_t rule_id) {
    for (size_t i = 0; i < pool->count; ++i) {
        if (pool->formulas[i].id == rule_id && pool->formulas[i].type == KF_TYPE_RULE) {
            pool->formulas[i].is_valid = 0;
            return 0;
        }
    }
    return -1;
}
