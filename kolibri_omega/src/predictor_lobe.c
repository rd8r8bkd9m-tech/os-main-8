#include "kolibri_omega/include/types.h"
#include "kolibri_omega/include/predictor_lobe.h"
#include "kolibri_omega/include/inference_engine.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include "kolibri_omega/include/canvas.h"
#include <stdio.h>

/**
 * @brief Инициализирует Лоб-Предсказатель.
 */
void omega_predictor_lobe_init(omega_predictor_lobe_t* lobe, omega_canvas_t* canvas, kf_pool_t* formula_pool) {
    lobe->canvas = canvas;
    lobe->formula_pool = formula_pool;
}

/**
 * @brief Выполняет один цикл работы Лоба-Предсказателя.
 */
void omega_predictor_lobe_tick(omega_predictor_lobe_t* lobe, int current_time) {
    // Блокировки мьютексов удалены для однопоточной модели

    // Проходим по всем элементам на Холсте
    for (size_t i = 0; i < lobe->canvas->count; ++i) {
        omega_canvas_item_t* item = &lobe->canvas->items[i];

        // Предсказываем только на основе фактов из прошлого или настоящего
        if (item->type == OMEGA_HYPOTHESIS_FACT && item->timestamp <= current_time) {
            // ========== PHASE 1: Single-step predictions (Одноступенчатые предсказания) ==========
            for (size_t j = 0; j < lobe->formula_pool->count; ++j) {
                kf_formula_t* rule = &lobe->formula_pool->formulas[j];
                if (rule->type == KF_TYPE_RULE && rule->is_valid) {
                    kf_formula_t predicted_formula;
                    if (kf_apply_rule_to_fact(lobe->formula_pool, rule->id, item->formula_id, &predicted_formula) == 0) {
                        
                        uint64_t predicted_formula_id = kf_add_formula(lobe->formula_pool, &predicted_formula);
                        if (predicted_formula_id > 0) {
                            omega_canvas_item_t prediction_item = {
                                .type = OMEGA_HYPOTHESIS_PREDICTION,
                                .formula_id = predicted_formula_id,
                                .derived_from_rule_id = rule->id,
                                .timestamp = predicted_formula.time,
                            };
                            omega_canvas_add_item(lobe->canvas, &prediction_item);
                        }
                    }
                }
            }
            
            // ========== PHASE 2: Multi-step inferences (Многоступенчатые выводы) ==========
            omega_inference_chain_t chains[5];
            int chain_count = omega_inference_forward_chain(lobe->formula_pool, item->formula_id, 
                                                            chains, 5, 3);
            
            for (int c = 0; c < chain_count; ++c) {
                omega_inference_chain_t* chain = &chains[c];
                
                // Создаем прямое правило из найденной цепочки для ускорения будущих предсказаний
                if (chain->chain_length > 1 && chain->confidence > 0.3) {
                    uint64_t shortcut_rule_id = omega_create_rule_from_chain(lobe->formula_pool, chain);
                    
                    if (shortcut_rule_id > 0) {
                        // Используем это новое правило для предсказания
                        kf_formula_t inferred_result;
                        if (kf_apply_rule_to_fact(lobe->formula_pool, shortcut_rule_id, 
                                                  item->formula_id, &inferred_result) == 0) {
                            uint64_t inferred_id = kf_add_formula(lobe->formula_pool, &inferred_result);
                            if (inferred_id > 0) {
                                omega_canvas_item_t inference_item = {
                                    .type = OMEGA_HYPOTHESIS_PREDICTION,
                                    .formula_id = inferred_id,
                                    .derived_from_rule_id = shortcut_rule_id,
                                    .timestamp = inferred_result.time,
                                };
                                omega_canvas_add_item(lobe->canvas, &inference_item);
                                
                                printf("[Predictor] Multi-step inference: created prediction %llu via chain of %zu rules (confidence: %.4f)\n",
                                       (unsigned long long)inferred_id, chain->chain_length, chain->confidence);
                            }
                        }
                    }
                }
            }
        }
    }

    // Блокировки мьютексов удалены для однопоточной модели
}
