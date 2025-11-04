#include "kolibri_omega/include/scenario_planner.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

typedef struct {
    omega_scenario_plan_t plans[OMEGA_MAX_PLANNING_DEPTH];
    int plan_count;
    
    omega_planning_stats_t stats;
} omega_planner_ctx_t;

static omega_planner_ctx_t planner_ctx = {0};

/**
 * omega_scenario_planner_init - инициализация
 */
int omega_scenario_planner_init(void) {
    memset(&planner_ctx, 0, sizeof(planner_ctx));
    
    printf("[ScenarioPlanner] Initialized with max %d plans, %d branches per plan\n",
           OMEGA_MAX_PLANNING_DEPTH, OMEGA_MAX_SCENARIO_BRANCHES);
    printf("[ScenarioPlanner] Multi-branch future modeling enabled\n");
    
    return 0;
}

/**
 * omega_create_scenario_plan - создать план
 */
uint32_t omega_create_scenario_plan(const char* plan_name,
                                   const omega_plan_state_t* current_state,
                                   int planning_depth) {
    if (planner_ctx.plan_count >= OMEGA_MAX_PLANNING_DEPTH) {
        return 0;
    }
    
    omega_scenario_plan_t* plan = &planner_ctx.plans[planner_ctx.plan_count];
    
    plan->plan_id = 8000 + planner_ctx.plan_count;
    strncpy(plan->plan_name, plan_name, sizeof(plan->plan_name) - 1);
    
    // Добавляем корневую ветвь (текущее состояние)
    omega_scenario_branch_t* root = &plan->branches[plan->branch_count];
    root->branch_id = 9000 + planner_ctx.plan_count * 100;
    root->parent_branch_id = 0;
    root->depth = 0;
    root->action = OMEGA_PLAN_WAIT;
    strcpy(root->action_description, "Current state");
    memcpy(&root->final_state, current_state, sizeof(omega_plan_state_t));
    root->expected_value = current_state->quality_score;
    root->confidence = 1.0;
    root->times_visited = 1;
    root->times_successful = 1;
    root->average_outcome = current_state->quality_score;
    
    plan->branch_count = 1;
    planner_ctx.plan_count++;
    planner_ctx.stats.total_plans_generated++;
    
    printf("[ScenarioPlanner] Created plan %u: \"%s\" with depth=%d, root_quality=%.2f\n",
           plan->plan_id, plan_name, planning_depth, current_state->quality_score);
    
    return plan->plan_id;
}

/**
 * omega_add_scenario_branch - добавить ветвь
 */
uint32_t omega_add_scenario_branch(uint32_t plan_id,
                                  uint32_t parent_branch_id,
                                  omega_planning_action_t action,
                                  const char* action_description) {
    // Найти план
    omega_scenario_plan_t* plan = NULL;
    for (int i = 0; i < planner_ctx.plan_count; i++) {
        if (planner_ctx.plans[i].plan_id == plan_id) {
            plan = &planner_ctx.plans[i];
            break;
        }
    }
    
    if (!plan || plan->branch_count >= OMEGA_MAX_SCENARIO_BRANCHES) {
        return 0;
    }
    
    // Найти parent branch для определения depth
    int parent_depth = 0;
    for (int i = 0; i < plan->branch_count; i++) {
        if (plan->branches[i].branch_id == parent_branch_id) {
            parent_depth = plan->branches[i].depth;
            break;
        }
    }
    
    // Создаем новую ветвь
    omega_scenario_branch_t* branch = &plan->branches[plan->branch_count];
    
    branch->branch_id = 9000 + planner_ctx.plan_count * 100 + plan->branch_count;
    branch->parent_branch_id = parent_branch_id;
    branch->depth = parent_depth + 1;
    branch->action = action;
    strncpy(branch->action_description, action_description, sizeof(branch->action_description) - 1);
    
    // Симулируем влияние действия на состояние
    // (упрощенная модель: действие влияет на metrics)
    switch (action) {
        case OMEGA_PLAN_ESCALATE:
            branch->final_state.divergence *= 1.2;
            branch->final_state.complexity *= 1.15;
            branch->final_state.quality_score *= 0.85;
            break;
        case OMEGA_PLAN_STABILIZE:
            branch->final_state.divergence *= 0.7;
            branch->final_state.complexity *= 0.8;
            branch->final_state.quality_score *= 1.1;
            break;
        case OMEGA_PLAN_ADAPT:
            branch->final_state.synchronization *= 1.05;
            branch->final_state.quality_score *= 1.05;
            break;
        case OMEGA_PLAN_EXPLORE:
            branch->final_state.complexity *= 1.3;
            branch->final_state.quality_score *= 1.0;  // Neutral
            break;
        case OMEGA_PLAN_COORDINATE:
            branch->final_state.coordination_level *= 1.2;
            branch->final_state.synchronization *= 1.1;
            branch->final_state.quality_score *= 1.08;
            break;
        case OMEGA_PLAN_WAIT:
        default:
            // Никаких изменений
            break;
    }
    
    // Clamp values to [0, 1]
    if (branch->final_state.divergence > 1.0) branch->final_state.divergence = 1.0;
    if (branch->final_state.complexity > 1.0) branch->final_state.complexity = 1.0;
    if (branch->final_state.quality_score > 1.0) branch->final_state.quality_score = 1.0;
    if (branch->final_state.quality_score < 0.0) branch->final_state.quality_score = 0.0;
    
    branch->expected_value = branch->final_state.quality_score;
    branch->confidence = 0.7;  // Меньше уверенности в предсказаниях
    branch->times_visited = 0;
    branch->times_successful = 0;
    branch->average_outcome = 0.0;
    
    plan->branch_count++;
    planner_ctx.stats.total_branches_explored++;
    
    printf("[ScenarioPlanner] Added branch %u: %s (action=%d, quality=%.2f)\n",
           branch->branch_id, action_description, action, branch->final_state.quality_score);
    
    return branch->branch_id;
}

/**
 * omega_compute_trajectory - вычислить траекторию
 */
uint32_t omega_compute_trajectory(uint32_t plan_id,
                                 uint32_t start_branch_id,
                                 const omega_plan_state_t* target_state,
                                 int max_steps) {
    omega_scenario_plan_t* plan = NULL;
    for (int i = 0; i < planner_ctx.plan_count; i++) {
        if (planner_ctx.plans[i].plan_id == plan_id) {
            plan = &planner_ctx.plans[i];
            break;
        }
    }
    
    if (!plan || plan->trajectory_count >= OMEGA_MAX_PLANNING_DEPTH) {
        return 0;
    }
    
    omega_plan_trajectory_t* traj = &plan->trajectories[plan->trajectory_count];
    traj->trajectory_id = 10000 + planner_ctx.plan_count * 100 + plan->trajectory_count;
    
    // Найти стартовое состояние
    omega_plan_state_t current = {0};
    for (int i = 0; i < plan->branch_count; i++) {
        if (plan->branches[i].branch_id == start_branch_id) {
            current = plan->branches[i].final_state;
            break;
        }
    }
    
    // Симулируем траекторию: приближаемся к target за max_steps шагов
    traj->length = 0;
    traj->total_cost = 0.0;
    traj->total_reward = 0.0;
    
    for (int step = 0; step < max_steps && traj->length < OMEGA_MAX_TRAJECTORY_POINTS; step++) {
        // Копируем текущее состояние в траекторию
        current.state_id = 10100 + step;
        current.depth = step;
        memcpy(&traj->states[traj->length], &current, sizeof(omega_plan_state_t));
        
        // Вычисляем ошибку до target
        double error = fabs(current.divergence - target_state->divergence) +
                      fabs(current.complexity - target_state->complexity) +
                      fabs(current.synchronization - target_state->synchronization);
        
        // Если ошибка мала, мы достигли цели
        if (error < 0.1) {
            traj->length++;
            traj->is_feasible = 1;
            break;
        }
        
        // Иначе: двигаемся к target (упрощенный градиентный спуск)
        double alpha = 0.1;  // Размер шага
        current.divergence += alpha * (target_state->divergence - current.divergence);
        current.complexity += alpha * (target_state->complexity - current.complexity);
        current.synchronization += alpha * (target_state->synchronization - current.synchronization);
        
        // Обновляем quality_score на основе прогресса
        current.quality_score = 1.0 - error / 3.0;
        
        traj->total_reward += current.quality_score;
        traj->total_cost += 1.0;
        traj->length++;
    }
    
    // Вычисляем вероятность успеха траектории
    if (traj->is_feasible) {
        traj->success_probability = 0.9;
    } else {
        traj->success_probability = 0.3;
    }
    
    traj->primary_action = OMEGA_PLAN_STABILIZE;  // Default action
    
    plan->trajectory_count++;
    planner_ctx.stats.total_trajectories_computed++;
    
    printf("[ScenarioPlanner] Computed trajectory %u: %d steps, feasible=%d, success_prob=%.2f\n",
           traj->trajectory_id, traj->length, traj->is_feasible, traj->success_probability);
    
    return traj->trajectory_id;
}

/**
 * omega_evaluate_branch - оценить ветвь
 * 
 * Upper Confidence Bound (UCB) для балансировки exploration/exploitation:
 * UCB = average_value + C * sqrt(log(N) / n)
 */
double omega_evaluate_branch(uint32_t plan_id, uint32_t branch_id) {
    omega_scenario_plan_t* plan = NULL;
    for (int i = 0; i < planner_ctx.plan_count; i++) {
        if (planner_ctx.plans[i].plan_id == plan_id) {
            plan = &planner_ctx.plans[i];
            break;
        }
    }
    
    if (!plan) return 0.0;
    
    // Найти ветвь
    omega_scenario_branch_t* branch = NULL;
    for (int i = 0; i < plan->branch_count; i++) {
        if (plan->branches[i].branch_id == branch_id) {
            branch = &plan->branches[i];
            break;
        }
    }
    
    if (!branch) return 0.0;
    
    // UCB formula
    double exploration_bonus = 0.0;
    if (branch->times_visited > 0) {
        exploration_bonus = 1.41 * sqrt(log(plan->branch_count + 1) / (double)branch->times_visited);
    } else {
        exploration_bonus = 10.0;  // Большой бонус для неизученных ветвей
    }
    
    branch->exploration_bonus = exploration_bonus;
    double ucb_value = branch->average_outcome + exploration_bonus;
    
    return ucb_value;
}

/**
 * omega_predict_outcome - предсказать результат
 */
int omega_predict_outcome(uint32_t plan_id,
                         uint32_t branch_id,
                         omega_plan_outcome_t* outcome_out) {
    if (!outcome_out) return -1;
    
    omega_scenario_plan_t* plan = NULL;
    for (int i = 0; i < planner_ctx.plan_count; i++) {
        if (planner_ctx.plans[i].plan_id == plan_id) {
            plan = &planner_ctx.plans[i];
            break;
        }
    }
    
    if (!plan) return -1;
    
    // Найти ветвь
    omega_scenario_branch_t* branch = NULL;
    for (int i = 0; i < plan->branch_count; i++) {
        if (plan->branches[i].branch_id == branch_id) {
            branch = &plan->branches[i];
            break;
        }
    }
    
    if (!branch) return -1;
    
    // Создать outcome
    outcome_out->outcome_id = 11000 + plan->outcome_count;
    snprintf(outcome_out->outcome_description, sizeof(outcome_out->outcome_description),
             "Outcome of %s", branch->action_description);
    
    outcome_out->probability = branch->confidence;
    outcome_out->final_divergence = branch->final_state.divergence;
    outcome_out->final_complexity = branch->final_state.complexity;
    outcome_out->final_synchronization = branch->final_state.synchronization;
    
    // Определяем, желателен ли результат
    double quality = branch->final_state.quality_score;
    outcome_out->desirability_score = quality;
    outcome_out->is_desirable = (quality > 0.6) ? 1 : 0;
    
    if (plan->outcome_count < OMEGA_MAX_OUTCOMES) {
        memcpy(&plan->outcomes[plan->outcome_count], outcome_out, sizeof(omega_plan_outcome_t));
        plan->outcome_count++;
    }
    
    planner_ctx.stats.total_outcomes_predicted++;
    
    printf("[ScenarioPlanner] Predicted outcome %u: prob=%.2f, desirable=%d, quality=%.2f\n",
           outcome_out->outcome_id, outcome_out->probability,
           outcome_out->is_desirable, outcome_out->desirability_score);
    
    return 0;
}

/**
 * omega_select_best_branch - выбрать лучшую ветвь
 */
uint32_t omega_select_best_branch(uint32_t plan_id) {
    omega_scenario_plan_t* plan = NULL;
    for (int i = 0; i < planner_ctx.plan_count; i++) {
        if (planner_ctx.plans[i].plan_id == plan_id) {
            plan = &planner_ctx.plans[i];
            break;
        }
    }
    
    if (!plan || plan->branch_count == 0) {
        return 0;
    }
    
    // Найти ветвь с максимальным expected value
    uint32_t best_branch_id = plan->branches[0].branch_id;
    double best_value = plan->branches[0].expected_value;
    
    for (int i = 1; i < plan->branch_count; i++) {
        double value = omega_evaluate_branch(plan_id, plan->branches[i].branch_id);
        if (value > best_value) {
            best_value = value;
            best_branch_id = plan->branches[i].branch_id;
        }
    }
    
    plan->recommended_branch = best_branch_id;
    
    printf("[ScenarioPlanner] Selected best branch %u with value=%.2f\n",
           best_branch_id, best_value);
    
    return best_branch_id;
}

/**
 * omega_expand_scenario_tree - расширить дерево
 */
int omega_expand_scenario_tree(uint32_t plan_id) {
    omega_scenario_plan_t* plan = NULL;
    for (int i = 0; i < planner_ctx.plan_count; i++) {
        if (planner_ctx.plans[i].plan_id == plan_id) {
            plan = &planner_ctx.plans[i];
            break;
        }
    }
    
    if (!plan) return -1;
    
    // Найти все листовые узлы (ветви без потомков)
    int leaves_expanded = 0;
    int initial_branch_count = plan->branch_count;
    
    for (int i = 0; i < initial_branch_count; i++) {
        // Генерируем новые ветви для каждого листового узла
        if (plan->branches[i].depth < 3) {  // Ограничение глубины
            // Добавляем 3-4 возможных действия
            omega_add_scenario_branch(plan_id, plan->branches[i].branch_id,
                                     OMEGA_PLAN_STABILIZE, "Stabilize system");
            omega_add_scenario_branch(plan_id, plan->branches[i].branch_id,
                                     OMEGA_PLAN_ADAPT, "Adapt parameters");
            omega_add_scenario_branch(plan_id, plan->branches[i].branch_id,
                                     OMEGA_PLAN_COORDINATE, "Coordinate agents");
            
            leaves_expanded++;
        }
    }
    
    planner_ctx.stats.average_branch_count = (double)plan->branch_count / (planner_ctx.plan_count + 1);
    planner_ctx.stats.average_plan_depth = 2.0;  // Hardcoded for demo
    
    printf("[ScenarioPlanner] Expanded tree: added %d new branches (total=%d)\n",
           plan->branch_count - initial_branch_count, plan->branch_count);
    
    return leaves_expanded;
}

/**
 * omega_simulate_plan_execution - симулировать выполнение
 */
int omega_simulate_plan_execution(uint32_t plan_id,
                                 omega_plan_trajectory_t* trajectory_out) {
    if (!trajectory_out) return -1;
    
    omega_scenario_plan_t* plan = NULL;
    for (int i = 0; i < planner_ctx.plan_count; i++) {
        if (planner_ctx.plans[i].plan_id == plan_id) {
            plan = &planner_ctx.plans[i];
            break;
        }
    }
    
    if (!plan || plan->trajectory_count == 0) {
        return -1;
    }
    
    // Копируем лучшую траекторию (или первую)
    memcpy(trajectory_out, &plan->trajectories[0], sizeof(omega_plan_trajectory_t));
    
    printf("[ScenarioPlanner] Simulated execution: trajectory %u with %d steps\n",
           plan->trajectories[0].trajectory_id, plan->trajectories[0].length);
    
    return 0;
}

/**
 * omega_get_planning_statistics - получить статистику
 */
const omega_planning_stats_t* omega_get_planning_statistics(void) {
    return &planner_ctx.stats;
}

/**
 * omega_scenario_planner_shutdown - остановка
 */
void omega_scenario_planner_shutdown(void) {
    const omega_planning_stats_t* stats = omega_get_planning_statistics();
    
    printf("[ScenarioPlanner] Shutdown: %d plans, %d branches explored\n",
           stats->total_plans_generated, stats->total_branches_explored);
    printf("  Trajectories: %d, Outcomes: %d\n",
           stats->total_trajectories_computed, stats->total_outcomes_predicted);
    printf("  Avg branch count: %.1f, Avg depth: %.1f, Avg trajectory: %.1f\n",
           stats->average_branch_count, stats->average_plan_depth,
           stats->average_trajectory_length);
    printf("  Best expected value: %.2f\n", stats->best_expected_value);
    
    memset(&planner_ctx, 0, sizeof(planner_ctx));
}
