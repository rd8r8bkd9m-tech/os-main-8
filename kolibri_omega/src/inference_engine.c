#include "kolibri_omega/include/inference_engine.h"
#include "kolibri_omega/include/types.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

/**
 * @brief Инициализирует модуль логического вывода.
 */
void omega_inference_engine_init(void) {
    printf("[InferenceEngine] Initialized. Ready for multi-step reasoning.\n");
}

/**
 * @brief Выполняет одноступенчатый логический вывод.
 */
uint64_t omega_inference_single_step(kf_pool_t* formula_pool, 
                                      uint64_t rule_id, 
                                      uint64_t fact_id,
                                      kf_formula_t* result) {
    kf_formula_t rule, fact;
    
    if (kf_get_formula(formula_pool, rule_id, &rule) != 0 || rule.type != KF_TYPE_RULE) {
        return 0;
    }
    
    if (kf_get_formula(formula_pool, fact_id, &fact) != 0 || fact.type != KF_TYPE_FACT) {
        return 0;
    }
    
    // Проверяем, применимо ли правило к факту
    if (rule.data.rule.condition_formula_id != fact_id) {
        return 0;  // Правило не применимо
    }
    
    // Получаем следствие правила
    kf_formula_t consequence;
    if (kf_get_formula(formula_pool, rule.data.rule.consequence_formula_id, &consequence) != 0) {
        return 0;
    }
    
    // Создаем результат с уверенностью, зависящей от правила
    *result = consequence;
    result->time = fact.time + 1;
    
    printf("[InferenceEngine] Single-step inference: fact %llu + rule %llu → consequence %llu (confidence: %.2f)\n",
           (unsigned long long)fact_id, (unsigned long long)rule_id, 
           (unsigned long long)consequence.id, rule.data.rule.confidence);
    
    return consequence.id;
}

/**
 * @brief Выполняет многоступенчатый логический вывод (forward chaining).
 */
int omega_inference_forward_chain(kf_pool_t* formula_pool,
                                   uint64_t initial_fact_id,
                                   omega_inference_chain_t* chains,
                                   size_t max_chains,
                                   int max_depth) {
    if (!formula_pool || !chains || max_chains == 0 || max_depth <= 0) {
        return 0;
    }
    
    int chain_count = 0;
    
    // Простой алгоритм forward chaining: для каждого факта найти применимые правила
    for (size_t i = 0; i < formula_pool->count && chain_count < max_chains; ++i) {
        kf_formula_t* rule = &formula_pool->formulas[i];
        
        if (rule->type != KF_TYPE_RULE || !rule->is_valid) {
            continue;
        }
        
        // Проверяем, применимо ли это правило к начальному факту
        if (rule->data.rule.condition_formula_id == initial_fact_id) {
            // Создаем новую цепочку
            omega_inference_chain_t* chain = &chains[chain_count];
            chain->rule_chain[0] = rule->id;
            chain->chain_length = 1;
            chain->initial_condition_id = initial_fact_id;
            chain->final_conclusion_id = rule->data.rule.consequence_formula_id;
            chain->confidence = rule->data.rule.confidence;
            
            // Пытаемся продолжить цепочку (рекурсивный поиск)
            if (max_depth > 1) {
                for (size_t j = 0; j < formula_pool->count && chain->chain_length < 10; ++j) {
                    kf_formula_t* next_rule = &formula_pool->formulas[j];
                    
                    if (next_rule->type != KF_TYPE_RULE || !next_rule->is_valid) {
                        continue;
                    }
                    
                    // Проверяем, применимо ли следующее правило к следствию текущего
                    if (next_rule->data.rule.condition_formula_id == chain->final_conclusion_id) {
                        chain->rule_chain[chain->chain_length] = next_rule->id;
                        chain->chain_length++;
                        chain->final_conclusion_id = next_rule->data.rule.consequence_formula_id;
                        chain->confidence *= next_rule->data.rule.confidence;
                        
                        printf("[InferenceEngine] Extended chain: rule %llu → %llu (new confidence: %.4f)\n",
                               (unsigned long long)rule->id, (unsigned long long)next_rule->id,
                               chain->confidence);
                    }
                }
            }
            
            printf("[InferenceEngine] Found inference chain of length %zu: %llu ⟹ %llu (confidence: %.4f)\n",
                   chain->chain_length, (unsigned long long)initial_fact_id, 
                   (unsigned long long)chain->final_conclusion_id, chain->confidence);
            
            chain_count++;
        }
    }
    
    return chain_count;
}

/**
 * @brief Вычисляет уверенность для цепочки правил.
 */
double omega_compute_chain_confidence(omega_inference_chain_t* chain, kf_pool_t* formula_pool) {
    if (!chain || chain->chain_length == 0) {
        return 0.0;
    }
    
    double total_confidence = 1.0;
    
    for (size_t i = 0; i < chain->chain_length; ++i) {
        kf_formula_t rule;
        if (kf_get_formula(formula_pool, chain->rule_chain[i], &rule) == 0 && rule.type == KF_TYPE_RULE) {
            total_confidence *= rule.data.rule.confidence;
        }
    }
    
    return total_confidence;
}

/**
 * @brief Создает новое правило на основе цепочки вывода.
 */
uint64_t omega_create_rule_from_chain(kf_pool_t* formula_pool, 
                                       omega_inference_chain_t* chain) {
    if (!chain || chain->chain_length == 0) {
        return 0;
    }
    
    // Создаем новое правило: начальное условие → конечное следствие
    kf_formula_t new_rule = {
        .type = KF_TYPE_RULE,
        .is_valid = 1,
        .time = 0,
        .data = {
            .rule = {
                .condition_formula_id = chain->initial_condition_id,
                .consequence_formula_id = chain->final_conclusion_id,
                .confidence = chain->confidence  // Уверенность = произведение
            }
        }
    };
    
    uint64_t rule_id = kf_add_formula(formula_pool, &new_rule);
    
    printf("[InferenceEngine] Created shortcut rule %llu from inference chain (length: %zu, confidence: %.4f)\n",
           (unsigned long long)rule_id, chain->chain_length, chain->confidence);
    
    return rule_id;
}
