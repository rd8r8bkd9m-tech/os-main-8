/**
 * policy_learner.h - Phase 8: Policy Learning from Counterfactuals
 *
 * Обучение оптимальной политики на основе гипотетических сценариев из Phase 6.
 * Система накапливает награды/штрафы за каждое вмешательство и учится
 * выбирать лучшие действия для минимизации divergence.
 */

#ifndef OMEGA_POLICY_LEARNER_H
#define OMEGA_POLICY_LEARNER_H

#include <stdint.h>

/* ========== Определения констант ========== */

#define OMEGA_MAX_POLICIES 20
#define OMEGA_MAX_POLICY_ACTIONS 100
#define OMEGA_MAX_LEARNING_EPISODES 500
#define OMEGA_MAX_STATE_SPACE 256

/* ========== Типы состояний ========== */

typedef enum {
    OMEGA_STATE_STABLE = 0,           // Система стабильна
    OMEGA_STATE_DIVERGING = 1,        // Расхождение растет
    OMEGA_STATE_HIGH_COMPLEXITY = 2,  // Сложность высока
    OMEGA_STATE_LOW_SYNC = 3,         // Низкая синхронизация
    OMEGA_STATE_CAUSAL_AMBIGUITY = 4  // Причинные связи неясны
} omega_system_state_t;

/* ========== Структуры данных ========== */

/**
 * omega_action_value_t - Оценка действия (Q-value)
 */
typedef struct {
    uint64_t action_id;
    int agent_id;
    uint64_t target_formula_id;
    
    double q_value;              // Q(state, action) - оценка действия
    double reward_sum;           // Сумма полученных наград
    int visit_count;             // Сколько раз это действие попробовано
    double average_reward;       // Средняя награда за действие
    
    int is_effective;            // 1 если действие обычно эффективно
} omega_action_value_t;

/**
 * omega_policy_t - Политика действий для состояния
 */
typedef struct {
    uint64_t policy_id;
    omega_system_state_t target_state;
    char policy_name[64];
    
    omega_action_value_t actions[OMEGA_MAX_POLICY_ACTIONS];
    int action_count;
    
    // Параметры обучения
    double learning_rate;       // α (alpha) - скорость обучения
    double exploration_rate;    // ε (epsilon) - вероятность исследования
    double discount_factor;     // γ (gamma) - фактор дисконтирования
    
    // Статистика
    int episodes_trained;
    double average_reward_per_episode;
    double win_rate;            // Доля успешных эпизодов
} omega_policy_t;

/**
 * omega_learning_episode_t - Эпизод обучения
 */
typedef struct {
    uint64_t episode_id;
    int episode_number;
    
    omega_system_state_t initial_state;
    uint64_t action_taken;
    double reward_received;
    omega_system_state_t next_state;
    
    double divergence_before;
    double divergence_after;
    
    int64_t episode_timestamp;
    int episode_length;  // Сколько шагов заняло
} omega_learning_episode_t;

/**
 * omega_policy_stats_t - Статистика обучения политики
 */
typedef struct {
    int total_policies;
    int active_policies;
    
    int total_episodes;
    int successful_episodes;  // Эпизоды с positive reward
    int failed_episodes;
    
    double average_reward;
    double cumulative_reward;
    double best_episode_reward;
    
    int policy_updates;
    int exploration_vs_exploitation;  // Ratio
    
    double average_q_value;
    double max_q_value;
} omega_policy_stats_t;

/* ========== API функции ========== */

/**
 * omega_policy_learner_init - инициализация системы обучения
 */
int omega_policy_learner_init(void);

/**
 * omega_create_policy - создать новую политику для состояния
 */
uint64_t omega_create_policy(omega_system_state_t state,
                            const char* policy_name,
                            double learning_rate);

/**
 * omega_record_learning_episode - записать эпизод обучения
 * 
 * После каждого сценария из Phase 6 записываем результат.
 */
int omega_record_learning_episode(omega_system_state_t initial_state,
                                 uint64_t action_taken,
                                 double reward,
                                 omega_system_state_t next_state,
                                 double divergence_delta);

/**
 * omega_compute_reward - вычислить награду за действие
 * 
 * Награда основана на улучшении divergence и других метриках.
 * @return Положительная награда (хорошо), отрицательная штраф (плохо)
 */
double omega_compute_reward(double divergence_before,
                           double divergence_after,
                           int num_interventions,
                           double intervention_cost);

/**
 * omega_select_best_action - выбрать лучшее действие для состояния
 * 
 * Использует epsilon-greedy стратегию:
 * - С вероятностью (1-epsilon): выбрать действие с максимальным Q
 * - С вероятностью epsilon: выбрать случайное действие (exploration)
 * 
 * @return ID лучшего действия или 0
 */
uint64_t omega_select_best_action(omega_system_state_t state,
                                 double exploration_epsilon);

/**
 * omega_update_policy - обновить Q-values политики
 * 
 * Использует Q-learning: Q_new = Q_old + α * (R + γ * max(Q_next) - Q_old)
 */
int omega_update_policy(omega_system_state_t state,
                       uint64_t action,
                       double reward,
                       omega_system_state_t next_state);

/**
 * omega_get_policy_effectiveness - оценить эффективность политики
 * 
 * @return Эффективность [0.0, 1.0] (win_rate)
 */
double omega_get_policy_effectiveness(omega_system_state_t state);

/**
 * omega_extract_best_policy_actions - извлечь лучшие действия
 * 
 * Возвращает массив наиболее эффективных действий для состояния.
 * @param actions_out - выходной массив ID действий
 * @param max_count - размер массива
 * @return Количество извлеченных действий
 */
int omega_extract_best_policy_actions(omega_system_state_t state,
                                     uint64_t* actions_out,
                                     int max_count);

/**
 * omega_get_policy_statistics - получить статистику
 */
const omega_policy_stats_t* omega_get_policy_statistics(void);

/**
 * omega_policy_learner_shutdown - остановка
 */
void omega_policy_learner_shutdown(void);

#endif // OMEGA_POLICY_LEARNER_H
