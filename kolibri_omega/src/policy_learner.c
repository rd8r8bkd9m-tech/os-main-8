#include "kolibri_omega/include/policy_learner.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define OMEGA_MAX_POLICY_INSTANCES 20

typedef struct {
    omega_policy_t policies[OMEGA_MAX_POLICIES];
    int policy_count;
    
    omega_learning_episode_t episodes[OMEGA_MAX_LEARNING_EPISODES];
    int episode_count;
    
    omega_policy_stats_t stats;
} omega_policy_ctx_t;

static omega_policy_ctx_t policy_ctx = {0};

/**
 * omega_policy_learner_init - инициализация
 */
int omega_policy_learner_init(void) {
    memset(&policy_ctx, 0, sizeof(policy_ctx));
    
    printf("[PolicyLearner] Initialized for learning up to %d policies\n",
           OMEGA_MAX_POLICIES);
    printf("[PolicyLearner] Q-learning framework with epsilon-greedy exploration\n");
    
    return 0;
}

/**
 * omega_create_policy - создать политику
 */
uint64_t omega_create_policy(omega_system_state_t state,
                            const char* policy_name,
                            double learning_rate) {
    if (policy_ctx.policy_count >= OMEGA_MAX_POLICIES) {
        return 0;
    }
    
    omega_policy_t* policy = &policy_ctx.policies[policy_ctx.policy_count];
    
    policy->policy_id = 10000 + policy_ctx.policy_count;
    policy->target_state = state;
    strncpy(policy->policy_name, policy_name, sizeof(policy->policy_name) - 1);
    policy->learning_rate = learning_rate;
    policy->exploration_rate = 0.2;  // 20% exploration
    policy->discount_factor = 0.99;  // 99% future reward discount
    
    policy_ctx.policy_count++;
    policy_ctx.stats.total_policies++;
    policy_ctx.stats.active_policies++;
    
    printf("[PolicyLearner] Created policy %lu: \"%s\" for state %d (α=%.2f)\n",
           (unsigned long)policy->policy_id, policy_name, state, learning_rate);
    
    return policy->policy_id;
}

/**
 * omega_record_learning_episode - записать эпизод
 */
int omega_record_learning_episode(omega_system_state_t initial_state,
                                 uint64_t action_taken,
                                 double reward,
                                 omega_system_state_t next_state,
                                 double divergence_delta) {
    if (policy_ctx.episode_count >= OMEGA_MAX_LEARNING_EPISODES) {
        return -1;
    }
    
    omega_learning_episode_t* episode = &policy_ctx.episodes[policy_ctx.episode_count];
    
    episode->episode_id = 11000 + policy_ctx.episode_count;
    episode->episode_number = policy_ctx.episode_count;
    episode->initial_state = initial_state;
    episode->action_taken = action_taken;
    episode->reward_received = reward;
    episode->next_state = next_state;
    episode->divergence_before = divergence_delta > 0 ? divergence_delta : 0.1;
    episode->divergence_after = fabs(divergence_delta * 0.5);
    
    policy_ctx.episode_count++;
    policy_ctx.stats.total_episodes++;
    
    if (reward > 0) {
        policy_ctx.stats.successful_episodes++;
    } else {
        policy_ctx.stats.failed_episodes++;
    }
    
    policy_ctx.stats.cumulative_reward += reward;
    
    if (reward > policy_ctx.stats.best_episode_reward) {
        policy_ctx.stats.best_episode_reward = reward;
    }
    
    return 0;
}

/**
 * omega_compute_reward - вычислить награду
 */
double omega_compute_reward(double divergence_before,
                           double divergence_after,
                           int num_interventions,
                           double intervention_cost) {
    // Базовая награда за улучшение divergence
    double improvement = divergence_before - divergence_after;
    double base_reward = improvement * 100.0;  // Scale: 1.0 divergence = 100 reward
    
    // Штраф за количество интервенций
    double intervention_penalty = num_interventions * intervention_cost * 10.0;
    
    // Итоговая награда
    double total_reward = base_reward - intervention_penalty;
    
    // Нормализуем к [-1, 1]
    if (total_reward > 10.0) total_reward = 10.0;
    if (total_reward < -10.0) total_reward = -10.0;
    
    return total_reward;
}

/**
 * omega_select_best_action - выбрать лучшее действие
 */
uint64_t omega_select_best_action(omega_system_state_t state,
                                 double exploration_epsilon) {
    // Найти политику для состояния
    omega_policy_t* target_policy = NULL;
    for (int i = 0; i < policy_ctx.policy_count; i++) {
        if (policy_ctx.policies[i].target_state == state && policy_ctx.policies[i].action_count > 0) {
            target_policy = &policy_ctx.policies[i];
            break;
        }
    }
    
    if (!target_policy) {
        return 0;  // Политика не найдена
    }
    
    // Epsilon-greedy выбор
    double rand_val = (double)rand() / RAND_MAX;
    
    if (rand_val < exploration_epsilon) {
        // Исследование: выбираем случайное действие
        int random_idx = rand() % target_policy->action_count;
        policy_ctx.stats.exploration_vs_exploitation++;
        return target_policy->actions[random_idx].action_id;
    } else {
        // Эксплуатация: выбираем действие с максимальным Q
        int best_idx = 0;
        double best_q = target_policy->actions[0].q_value;
        
        for (int i = 1; i < target_policy->action_count; i++) {
            if (target_policy->actions[i].q_value > best_q) {
                best_q = target_policy->actions[i].q_value;
                best_idx = i;
            }
        }
        
        return target_policy->actions[best_idx].action_id;
    }
}

/**
 * omega_update_policy - обновить политику (Q-learning)
 */
int omega_update_policy(omega_system_state_t state,
                       uint64_t action,
                       double reward,
                       omega_system_state_t next_state) {
    // Найти политику для текущего состояния
    omega_policy_t* policy = NULL;
    for (int i = 0; i < policy_ctx.policy_count; i++) {
        if (policy_ctx.policies[i].target_state == state) {
            policy = &policy_ctx.policies[i];
            break;
        }
    }
    
    if (!policy) {
        return -1;
    }
    
    // Найти или создать action-value для этого действия
    omega_action_value_t* action_value = NULL;
    int action_idx = -1;
    
    for (int i = 0; i < policy->action_count; i++) {
        if (policy->actions[i].action_id == action) {
            action_value = &policy->actions[i];
            action_idx = i;
            break;
        }
    }
    
    // Если действия нет, добавляем новое
    if (!action_value && policy->action_count < OMEGA_MAX_POLICY_ACTIONS) {
        action_value = &policy->actions[policy->action_count];
        action_value->action_id = action;
        action_value->q_value = 0.0;
        action_value->reward_sum = 0.0;
        action_value->visit_count = 0;
        action_idx = policy->action_count;
        policy->action_count++;
    }
    
    if (!action_value) {
        return -1;  // Невозможно добавить действие
    }
    
    // Находим max Q для next_state
    double max_q_next = 0.0;
    omega_policy_t* next_policy = NULL;
    for (int i = 0; i < policy_ctx.policy_count; i++) {
        if (policy_ctx.policies[i].target_state == next_state) {
            next_policy = &policy_ctx.policies[i];
            break;
        }
    }
    
    if (next_policy && next_policy->action_count > 0) {
        max_q_next = next_policy->actions[0].q_value;
        for (int i = 1; i < next_policy->action_count; i++) {
            if (next_policy->actions[i].q_value > max_q_next) {
                max_q_next = next_policy->actions[i].q_value;
            }
        }
    }
    
    // Q-learning update: Q_new = Q_old + α * (R + γ * max(Q_next) - Q_old)
    double old_q = action_value->q_value;
    double q_target = reward + (policy->discount_factor * max_q_next);
    action_value->q_value = old_q + (policy->learning_rate * (q_target - old_q));
    
    // Обновляем статистику действия
    action_value->reward_sum += reward;
    action_value->visit_count++;
    action_value->average_reward = action_value->reward_sum / action_value->visit_count;
    
    if (action_value->average_reward > 0.5) {
        action_value->is_effective = 1;
    }
    
    policy->episodes_trained++;
    policy->average_reward_per_episode = action_value->average_reward;
    policy->win_rate = (double)action_value->visit_count / (action_value->visit_count + 1);
    
    policy_ctx.stats.policy_updates++;
    policy_ctx.stats.average_q_value += action_value->q_value;
    
    if (action_value->q_value > policy_ctx.stats.max_q_value) {
        policy_ctx.stats.max_q_value = action_value->q_value;
    }
    
    return 0;
}

/**
 * omega_get_policy_effectiveness - оценить эффективность политики
 */
double omega_get_policy_effectiveness(omega_system_state_t state) {
    omega_policy_t* policy = NULL;
    for (int i = 0; i < policy_ctx.policy_count; i++) {
        if (policy_ctx.policies[i].target_state == state) {
            policy = &policy_ctx.policies[i];
            break;
        }
    }
    
    if (!policy || policy->episodes_trained == 0) {
        return 0.0;
    }
    
    return policy->win_rate;
}

/**
 * omega_extract_best_policy_actions - извлечь лучшие действия
 */
int omega_extract_best_policy_actions(omega_system_state_t state,
                                     uint64_t* actions_out,
                                     int max_count) {
    if (!actions_out || max_count <= 0) {
        return 0;
    }
    
    omega_policy_t* policy = NULL;
    for (int i = 0; i < policy_ctx.policy_count; i++) {
        if (policy_ctx.policies[i].target_state == state) {
            policy = &policy_ctx.policies[i];
            break;
        }
    }
    
    if (!policy || policy->action_count == 0) {
        return 0;
    }
    
    // Сортируем действия по Q-value (пузырьком)
    int indices[OMEGA_MAX_POLICY_ACTIONS];
    for (int i = 0; i < policy->action_count; i++) {
        indices[i] = i;
    }
    
    for (int i = 0; i < policy->action_count - 1; i++) {
        for (int j = 0; j < policy->action_count - i - 1; j++) {
            if (policy->actions[indices[j]].q_value < policy->actions[indices[j + 1]].q_value) {
                int tmp = indices[j];
                indices[j] = indices[j + 1];
                indices[j + 1] = tmp;
            }
        }
    }
    
    // Заполняем выходной массив
    int count = (policy->action_count < max_count) ? policy->action_count : max_count;
    for (int i = 0; i < count; i++) {
        actions_out[i] = policy->actions[indices[i]].action_id;
    }
    
    return count;
}

/**
 * omega_get_policy_statistics - получить статистику
 */
const omega_policy_stats_t* omega_get_policy_statistics(void) {
    if (policy_ctx.stats.total_episodes > 0) {
        policy_ctx.stats.average_reward = policy_ctx.stats.cumulative_reward / policy_ctx.stats.total_episodes;
        policy_ctx.stats.average_q_value = policy_ctx.stats.average_q_value / (policy_ctx.stats.policy_updates + 1);
    }
    
    return &policy_ctx.stats;
}

/**
 * omega_policy_learner_shutdown - остановка
 */
void omega_policy_learner_shutdown(void) {
    const omega_policy_stats_t* stats = omega_get_policy_statistics();
    
    printf("[PolicyLearner] Shutdown: %d policies, %d total episodes\n",
           policy_ctx.policy_count, stats->total_episodes);
    printf("  Successful: %d, Failed: %d\n",
           stats->successful_episodes, stats->failed_episodes);
    printf("  Average reward: %.2f, Best: %.2f\n",
           stats->average_reward, stats->best_episode_reward);
    printf("  Policy updates: %d, Average Q-value: %.3f\n",
           stats->policy_updates, stats->average_q_value);
    
    memset(&policy_ctx, 0, sizeof(policy_ctx));
}
