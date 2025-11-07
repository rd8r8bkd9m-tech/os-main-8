#include "kolibri_omega/include/counterfactual_reasoner.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define OMEGA_MAX_SCENARIO_INSTANCES 50

typedef struct {
    omega_scenario_t scenarios[OMEGA_MAX_SCENARIOS];
    int scenario_count;
    
    omega_causal_link_t causal_links[OMEGA_MAX_CAUSAL_LINKS];
    int causal_link_count;
    
    omega_branch_t branches[OMEGA_MAX_BRANCHES];
    int branch_count;
    
    omega_counterfactual_stats_t stats;
} omega_counterfactual_ctx_t;

static omega_counterfactual_ctx_t cf_ctx = {0};

/**
 * omega_counterfactual_reasoner_init - инициализация
 */
int omega_counterfactual_reasoner_init(void) {
    memset(&cf_ctx, 0, sizeof(cf_ctx));
    
    printf("[CounterfactualReasoner] Initialized for analyzing up to %d scenarios\n",
           OMEGA_MAX_SCENARIOS);
    printf("[CounterfactualReasoner] Max interventions per scenario: %d\n",
           OMEGA_MAX_INTERVENTIONS);
    
    return 0;
}

/**
 * omega_create_scenario - создать новый сценарий
 */
uint64_t omega_create_scenario(const char* scenario_name, int64_t divergence_timestamp) {
    if (cf_ctx.scenario_count >= OMEGA_MAX_SCENARIOS || !scenario_name) {
        return 0;
    }
    
    omega_scenario_t* scenario = &cf_ctx.scenarios[cf_ctx.scenario_count];
    
    scenario->scenario_id = 5000 + cf_ctx.scenario_count;
    strncpy(scenario->scenario_name, scenario_name, OMEGA_SCENARIO_NAME_LEN - 1);
    scenario->divergence_timestamp = divergence_timestamp;
    scenario->intervention_count = 0;
    scenario->is_active = 1;
    
    cf_ctx.scenario_count++;
    cf_ctx.stats.total_scenarios++;
    cf_ctx.stats.active_scenarios++;
    
    printf("[CounterfactualReasoner] Created scenario %lu: \"%s\" (divergence at %ld)\n",
           (unsigned long)scenario->scenario_id, scenario_name, (long)divergence_timestamp);
    
    return scenario->scenario_id;
}

/**
 * omega_add_intervention - добавить вмешательство в сценарий
 */
int omega_add_intervention(uint64_t scenario_id, omega_intervention_type_t type,
                          uint32_t target_agent_id, uint64_t target_formula_id,
                          double strength, const char* description) {
    // Найти сценарий
    omega_scenario_t* scenario = NULL;
    for (int i = 0; i < cf_ctx.scenario_count; i++) {
        if (cf_ctx.scenarios[i].scenario_id == scenario_id) {
            scenario = &cf_ctx.scenarios[i];
            break;
        }
    }
    
    if (!scenario || scenario->intervention_count >= OMEGA_MAX_INTERVENTIONS) {
        return -1;
    }
    
    omega_intervention_t* intervention = &scenario->interventions[scenario->intervention_count];
    
    intervention->intervention_id = 6000 + scenario->intervention_count;
    intervention->intervention_type = type;
    intervention->target_agent_id = target_agent_id;
    intervention->target_formula_id = target_formula_id;
    intervention->intervention_strength = strength;
    intervention->apply_at_timestamp = scenario->divergence_timestamp;
    strncpy(intervention->description, description, sizeof(intervention->description) - 1);
    
    scenario->intervention_count++;
    cf_ctx.stats.total_interventions_tested++;
    
    if (strength > 0.7) {
        cf_ctx.stats.high_impact_interventions++;
    }
    
    printf("[CounterfactualReasoner] Added intervention: %s (strength: %.2f)\n",
           description, strength);
    
    return 0;
}

/**
 * omega_analyze_scenario_branch - проанализировать ветвь
 */
uint64_t omega_analyze_scenario_branch(uint64_t parent_scenario_id, int depth) {
    if (cf_ctx.branch_count >= OMEGA_MAX_BRANCHES) {
        return 0;
    }
    
    omega_branch_t* branch = &cf_ctx.branches[cf_ctx.branch_count];
    
    branch->branch_id = 7000 + cf_ctx.branch_count;
    branch->parent_scenario_id = parent_scenario_id;
    branch->depth = depth;
    branch->num_children = 0;
    
    // Вероятность зависит от глубины: чем глубже, тем ниже вероятность альтернативы
    branch->branch_probability = 1.0 / (1.0 + depth * 0.3);
    
    // Совокупный импакт - произведение вероятностей вмешательств
    branch->cumulative_impact = branch->branch_probability;
    
    // Найти родительский сценарий для вычисления импакта
    if (parent_scenario_id > 0) {
        for (int i = 0; i < cf_ctx.scenario_count; i++) {
            if (cf_ctx.scenarios[i].scenario_id == parent_scenario_id) {
                for (int j = 0; j < cf_ctx.scenarios[i].intervention_count; j++) {
                    branch->cumulative_impact *= 
                        (1.0 - cf_ctx.scenarios[i].interventions[j].intervention_strength);
                }
                break;
            }
        }
    }
    
    cf_ctx.branch_count++;
    cf_ctx.stats.branches_explored++;
    
    if (branch->branch_probability > cf_ctx.stats.max_branch_probability) {
        cf_ctx.stats.max_branch_probability = branch->branch_probability;
    }
    
    printf("[CounterfactualReasoner] Analyzed branch %lu (depth: %d, prob: %.3f)\n",
           (unsigned long)branch->branch_id, depth, branch->branch_probability);
    
    return branch->branch_id;
}

/**
 * omega_apply_interventions - применить вмешательства
 */
int omega_apply_interventions(uint64_t scenario_id) {
    omega_scenario_t* scenario = NULL;
    
    for (int i = 0; i < cf_ctx.scenario_count; i++) {
        if (cf_ctx.scenarios[i].scenario_id == scenario_id) {
            scenario = &cf_ctx.scenarios[i];
            break;
        }
    }
    
    if (!scenario) {
        return -1;
    }
    
    // Симулируем эффекты вмешательств
    // В реальной системе здесь была бы комплексная логика
    
    double total_effect = 0.0;
    for (int i = 0; i < scenario->intervention_count; i++) {
        total_effect += scenario->interventions[i].intervention_strength * 0.1;
    }
    
    // Ожидаемые исходы основаны на вмешательствах
    scenario->expected_canvas_items = 100.0 + (total_effect * 50.0);
    scenario->expected_agent_sync = 0.5 + (total_effect * 0.3);
    scenario->expected_pattern_count = 10.0 + (total_effect * 20.0);
    
    // Симулируем реальные результаты (с некоторой вариативностью)
    scenario->actual_canvas_items = scenario->expected_canvas_items * (0.9 + (rand() % 20) / 100.0);
    scenario->actual_agent_sync = scenario->expected_agent_sync * (0.9 + (rand() % 20) / 100.0);
    scenario->actual_pattern_count = scenario->expected_pattern_count * (0.9 + (rand() % 20) / 100.0);
    
    printf("[CounterfactualReasoner] Applied %d interventions to scenario %lu\n",
           scenario->intervention_count, (unsigned long)scenario_id);
    printf("  Expected: %.0f canvas items, %.2f agent sync, %.0f patterns\n",
           scenario->expected_canvas_items, scenario->expected_agent_sync,
           scenario->expected_pattern_count);
    printf("  Actual: %.0f canvas items, %.2f agent sync, %.0f patterns\n",
           scenario->actual_canvas_items, scenario->actual_agent_sync,
           scenario->actual_pattern_count);
    
    return 1;
}

/**
 * omega_detect_causal_links - обнаружить причинные связи
 */
int omega_detect_causal_links(uint64_t scenario_id) {
    if (cf_ctx.causal_link_count >= OMEGA_MAX_CAUSAL_LINKS) {
        return 0;
    }
    
    // Создаем гипотетические причинные связи на основе интервенций
    omega_scenario_t* scenario = NULL;
    for (int i = 0; i < cf_ctx.scenario_count; i++) {
        if (cf_ctx.scenarios[i].scenario_id == scenario_id) {
            scenario = &cf_ctx.scenarios[i];
            break;
        }
    }
    
    if (!scenario || scenario->intervention_count == 0) {
        return 0;
    }
    
    int new_links = 0;
    
    // Для каждой пары вмешательств создаем возможную причинную связь
    for (int i = 0; i < scenario->intervention_count - 1 && 
         cf_ctx.causal_link_count < OMEGA_MAX_CAUSAL_LINKS; i++) {
        
        omega_causal_link_t* link = &cf_ctx.causal_links[cf_ctx.causal_link_count];
        
        link->link_id = 8000 + cf_ctx.causal_link_count;
        link->cause_formula_id = scenario->interventions[i].target_formula_id;
        link->effect_formula_id = scenario->interventions[i + 1].target_formula_id;
        
        // Тип причинности зависит от силы вмешательства
        if (scenario->interventions[i].intervention_strength > 0.8) {
            link->causality_type = OMEGA_CAUSALITY_DIRECT;
        } else if (scenario->interventions[i].intervention_strength > 0.5) {
            link->causality_type = OMEGA_CAUSALITY_INDIRECT;
        } else {
            link->causality_type = OMEGA_CAUSALITY_CORRELATION;
        }
        
        link->strength = scenario->interventions[i].intervention_strength * 0.8;
        link->observed_delay_ms = 10 + (i * 5);
        link->confirmed = 0;  // Гипотетическая связь
        
        cf_ctx.causal_link_count++;
        cf_ctx.stats.causal_links_discovered++;
        new_links++;
    }
    
    printf("[CounterfactualReasoner] Detected %d causal links for scenario %lu\n",
           new_links, (unsigned long)scenario_id);
    
    return new_links;
}

/**
 * omega_compute_divergence - вычислить расхождение
 */
double omega_compute_divergence(uint64_t scenario_id) {
    omega_scenario_t* scenario = NULL;
    
    for (int i = 0; i < cf_ctx.scenario_count; i++) {
        if (cf_ctx.scenarios[i].scenario_id == scenario_id) {
            scenario = &cf_ctx.scenarios[i];
            break;
        }
    }
    
    if (!scenario) {
        return 0.0;
    }
    
    // Вычисляем расхождение между ожидаемым и фактическим
    double divergence_canvas = fabs(scenario->actual_canvas_items - scenario->expected_canvas_items) / 
                               (scenario->expected_canvas_items + 1);
    double divergence_sync = fabs(scenario->actual_agent_sync - scenario->expected_agent_sync);
    double divergence_patterns = fabs(scenario->actual_pattern_count - scenario->expected_pattern_count) / 
                                 (scenario->expected_pattern_count + 1);
    
    // Средневзвешенное расхождение
    scenario->divergence_ratio = (divergence_canvas * 0.4 + 
                                  divergence_sync * 0.3 + 
                                  divergence_patterns * 0.3);
    
    // Нормализуем до [0, 1]
    scenario->divergence_ratio = (scenario->divergence_ratio > 1.0) ? 1.0 : scenario->divergence_ratio;
    
    scenario->outcome_consistent = (scenario->divergence_ratio < 0.1) ? 1 : 0;
    
    cf_ctx.stats.average_divergence += scenario->divergence_ratio;
    if (scenario->divergence_ratio > cf_ctx.stats.largest_divergence) {
        cf_ctx.stats.largest_divergence = scenario->divergence_ratio;
    }
    
    printf("[CounterfactualReasoner] Divergence for scenario %lu: %.3f %s\n",
           (unsigned long)scenario_id, scenario->divergence_ratio,
           scenario->outcome_consistent ? "(consistent)" : "(diverged)");
    
    return scenario->divergence_ratio;
}

/**
 * omega_rank_scenarios_by_impact - ранжировать сценарии
 */
int omega_rank_scenarios_by_impact(uint64_t* scenario_ids_out, int max_count) {
    if (!scenario_ids_out || max_count <= 0) {
        return 0;
    }
    
    // Простая сортировка: по количеству интервенций и их силе
    int count = (cf_ctx.scenario_count < max_count) ? cf_ctx.scenario_count : max_count;
    
    // Создаем список индексов отсортированных по импакту
    int indices[OMEGA_MAX_SCENARIOS];
    for (int i = 0; i < cf_ctx.scenario_count; i++) {
        indices[i] = i;
    }
    
    // Простая сортировка пузырьком по интервенциям
    for (int i = 0; i < cf_ctx.scenario_count - 1; i++) {
        for (int j = 0; j < cf_ctx.scenario_count - i - 1; j++) {
            int idx1 = indices[j];
            int idx2 = indices[j + 1];
            
            int impact1 = cf_ctx.scenarios[idx1].intervention_count;
            int impact2 = cf_ctx.scenarios[idx2].intervention_count;
            
            if (impact1 < impact2) {
                indices[j] = idx2;
                indices[j + 1] = idx1;
            }
        }
    }
    
    // Заполняем выходной массив
    for (int i = 0; i < count; i++) {
        scenario_ids_out[i] = cf_ctx.scenarios[indices[i]].scenario_id;
    }
    
    printf("[CounterfactualReasoner] Ranked %d scenarios by impact\n", count);
    
    return count;
}

/**
 * omega_get_counterfactual_statistics - получить статистику
 */
const omega_counterfactual_stats_t* omega_get_counterfactual_statistics(void) {
    cf_ctx.stats.active_scenarios = 0;
    for (int i = 0; i < cf_ctx.scenario_count; i++) {
        if (cf_ctx.scenarios[i].is_active) {
            cf_ctx.stats.active_scenarios++;
        }
    }
    
    if (cf_ctx.scenario_count > 0) {
        cf_ctx.stats.average_divergence /= cf_ctx.scenario_count;
    }
    
    cf_ctx.stats.scenarios_completed = cf_ctx.scenario_count - cf_ctx.stats.active_scenarios;
    
    return &cf_ctx.stats;
}

/**
 * omega_counterfactual_reasoner_shutdown - остановка
 */
void omega_counterfactual_reasoner_shutdown(void) {
    printf("[CounterfactualReasoner] Shutdown: %d scenarios, %d interventions, "
           "%d causal links, %d branches\n",
           cf_ctx.scenario_count, cf_ctx.stats.total_interventions_tested,
           cf_ctx.causal_link_count, cf_ctx.branch_count);
    printf("[CounterfactualReasoner] High-impact interventions: %d\n",
           cf_ctx.stats.high_impact_interventions);
    printf("[CounterfactualReasoner] Average divergence: %.3f, Max: %.3f\n",
           cf_ctx.stats.average_divergence, cf_ctx.stats.largest_divergence);
    
    memset(&cf_ctx, 0, sizeof(cf_ctx));
}
