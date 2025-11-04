#include "kolibri_omega/include/learning_engine.h"
#include "kolibri_omega/include/self_reflection.h"
#include "kolibri_omega/include/types.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include <stdio.h>
#include <math.h>

/**
 * @brief Обновляет уверенность правила (adaptive learning).
 */
void omega_update_rule_confidence(kf_pool_t* formula_pool, uint64_t rule_id, int was_correct) {
    kf_formula_t rule;
    if (kf_get_formula(formula_pool, rule_id, &rule) != 0 || rule.type != KF_TYPE_RULE) {
        return;
    }

    // Отмечаем применение правила для self-reflection
    omega_mark_rule_applied(rule_id);
    
    // Отмечаем верификацию или противоречие
    if (was_correct) {
        omega_mark_rule_verified(rule_id);
    } else {
        omega_mark_rule_contradicted(rule_id);
    }

    // Экспоненциальное скользящее среднее для уверенности
    double new_value = was_correct ? 1.0 : 0.0;
    double alpha = 0.1;  // Коэффициент обучения
    rule.data.rule.confidence = rule.data.rule.confidence * (1.0 - alpha) + new_value * alpha;

    // Клампируем значение в диапазон [0.0, 1.0]
    if (rule.data.rule.confidence > 1.0) rule.data.rule.confidence = 1.0;
    if (rule.data.rule.confidence < 0.0) rule.data.rule.confidence = 0.0;

    // Обновляем правило в пуле
    for (size_t i = 0; i < formula_pool->count; ++i) {
        if (formula_pool->formulas[i].id == rule_id) {
            formula_pool->formulas[i].data.rule.confidence = rule.data.rule.confidence;
            printf("[LearningEngine] Updated confidence of rule %llu to %.2f\n",
                   (unsigned long long)rule_id, rule.data.rule.confidence);
            return;
        }
    }
}

/**
 * @brief Вычисляет точность правила.
 */
double omega_calculate_rule_accuracy(kf_pool_t* formula_pool, uint64_t rule_id) {
    kf_formula_t rule;
    if (kf_get_formula(formula_pool, rule_id, &rule) != 0 || rule.type != KF_TYPE_RULE) {
        return 0.0;
    }
    return rule.data.rule.confidence;
}

/**
 * @brief Ранжирует правила по уверенности (для будущего использования в предсказателе).
 */
void omega_rank_rules_by_confidence(kf_pool_t* formula_pool) {
    if (!formula_pool || formula_pool->count == 0) {
        return;
    }

    // Простая сортировка пузырьком для демонстрации
    for (size_t i = 0; i < formula_pool->count; ++i) {
        for (size_t j = i + 1; j < formula_pool->count; ++j) {
            kf_formula_t* rule_i = &formula_pool->formulas[i];
            kf_formula_t* rule_j = &formula_pool->formulas[j];

            // Сравниваем только правила
            if (rule_i->type == KF_TYPE_RULE && rule_j->type == KF_TYPE_RULE) {
                if (rule_i->data.rule.confidence < rule_j->data.rule.confidence) {
                    // Меняем местами
                    kf_formula_t temp = *rule_i;
                    *rule_i = *rule_j;
                    *rule_j = temp;
                }
            }
        }
    }

    printf("[LearningEngine] Rules ranked by confidence\n");
}
