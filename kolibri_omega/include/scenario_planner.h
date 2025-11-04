#ifndef OMEGA_SCENARIO_PLANNER_H
#define OMEGA_SCENARIO_PLANNER_H

#include <stdint.h>

/* ========== Константы ========== */
#define OMEGA_MAX_SCENARIO_BRANCHES 100
#define OMEGA_MAX_PLANNING_DEPTH 20
#define OMEGA_MAX_TRAJECTORY_POINTS 500
#define OMEGA_MAX_PLAN_STATES 50
#define OMEGA_MAX_OUTCOMES 200

/* ========== Перечисления ========== */

/**
 * omega_planning_action_t - действие при планировании
 */
typedef enum {
    OMEGA_PLAN_WAIT = 0,           // Ничего не делать
    OMEGA_PLAN_ESCALATE = 1,       // Увеличить активность
    OMEGA_PLAN_STABILIZE = 2,      // Стабилизировать
    OMEGA_PLAN_ADAPT = 3,          // Адаптировать параметры
    OMEGA_PLAN_EXPLORE = 4,        // Исследовать новые стратегии
    OMEGA_PLAN_COORDINATE = 5      // Координировать агентов
} omega_planning_action_t;

/* ========== Структуры данных ========== */

/**
 * omega_plan_state_t - состояние при планировании
 * 
 * Представляет моментальный снимок системы в точке плана
 */
typedef struct {
    uint32_t state_id;
    int depth;  // Глубина в дереве плана (0 = текущее состояние)
    uint64_t timestamp_ms;
    
    // Системные метрики
    double divergence;
    double complexity;
    double synchronization;
    double coordination_level;
    
    // Предсказанные значения
    double predicted_next_divergence;
    double predicted_stability_score;
    
    // Оценка состояния
    double quality_score;  // 0..1, 1 = идеально
    int is_goal_state;
} omega_plan_state_t;

/**
 * omega_plan_trajectory_t - траектория в пространстве состояний
 * 
 * Последовательность состояний через временные шаги
 */
typedef struct {
    uint32_t trajectory_id;
    
    // Путь через состояния
    omega_plan_state_t states[OMEGA_MAX_TRAJECTORY_POINTS];
    int length;  // Количество точек траектории
    
    // Интегральные метрики
    double total_cost;         // Сумма затрат
    double total_reward;       // Сумма вознаграждений
    double success_probability; // P(trajectory leads to goal)
    
    // Характеристика
    int is_feasible;
    omega_planning_action_t primary_action;
} omega_plan_trajectory_t;

/**
 * omega_scenario_branch_t - ветвь сценария в дереве планирования
 */
typedef struct {
    uint32_t branch_id;
    uint32_t parent_branch_id;
    int depth;
    
    // Действие, ведущее к этой ветви
    omega_planning_action_t action;
    char action_description[128];
    
    // Состояние в конце ветви
    omega_plan_state_t final_state;
    
    // Оценка ветви
    double expected_value;      // Expected utility of this branch
    double exploration_bonus;   // Bonus for unexplored areas (UCB)
    double confidence;          // Confidence in prediction (0..1)
    
    // Результаты
    int times_visited;
    int times_successful;
    double average_outcome;
} omega_scenario_branch_t;

/**
 * omega_plan_outcome_t - итоговый результат плана
 */
typedef struct {
    uint32_t outcome_id;
    
    // Описание
    char outcome_description[256];
    
    // Вероятность результата
    double probability;
    
    // Прогноз на конечное состояние
    double final_divergence;
    double final_complexity;
    double final_synchronization;
    
    // Оценка (хорошо ли это?)
    int is_desirable;
    double desirability_score;
} omega_plan_outcome_t;

/**
 * omega_scenario_plan_t - полный план с ветвлениями
 */
typedef struct {
    uint32_t plan_id;
    char plan_name[128];
    
    // Дерево сценариев
    omega_scenario_branch_t branches[OMEGA_MAX_SCENARIO_BRANCHES];
    int branch_count;
    
    // Траектории
    omega_plan_trajectory_t trajectories[OMEGA_MAX_PLANNING_DEPTH];
    int trajectory_count;
    
    // Возможные результаты
    omega_plan_outcome_t outcomes[OMEGA_MAX_OUTCOMES];
    int outcome_count;
    
    // Итоговая оценка плана
    double total_expected_value;
    int recommended_branch;
} omega_scenario_plan_t;

/**
 * omega_planning_stats_t - статистика планирования
 */
typedef struct {
    int total_plans_generated;
    int total_branches_explored;
    int total_trajectories_computed;
    int total_outcomes_predicted;
    
    double average_plan_depth;
    double average_branch_count;
    double average_trajectory_length;
    
    int best_outcome_index;
    double best_expected_value;
    
    int exploration_vs_exploitation_ratio;
} omega_planning_stats_t;

/* ========== API функции ========== */

/**
 * omega_scenario_planner_init - инициализация планировщика
 */
int omega_scenario_planner_init(void);

/**
 * omega_create_scenario_plan - создать новый план сценариев
 */
uint32_t omega_create_scenario_plan(const char* plan_name,
                                   const omega_plan_state_t* current_state,
                                   int planning_depth);

/**
 * omega_add_scenario_branch - добавить ветвь к плану
 */
uint32_t omega_add_scenario_branch(uint32_t plan_id,
                                  uint32_t parent_branch_id,
                                  omega_planning_action_t action,
                                  const char* action_description);

/**
 * omega_compute_trajectory - вычислить траекторию от current до target
 * 
 * Использует предсказатели и политики для моделирования пути
 */
uint32_t omega_compute_trajectory(uint32_t plan_id,
                                 uint32_t start_branch_id,
                                 const omega_plan_state_t* target_state,
                                 int max_steps);

/**
 * omega_evaluate_branch - оценить ветвь с помощью UCB или ожидаемой стоимости
 */
double omega_evaluate_branch(uint32_t plan_id, uint32_t branch_id);

/**
 * omega_predict_outcome - предсказать итоговый результат для ветви
 */
int omega_predict_outcome(uint32_t plan_id,
                         uint32_t branch_id,
                         omega_plan_outcome_t* outcome_out);

/**
 * omega_select_best_branch - выбрать лучшую ветвь по expected value
 */
uint32_t omega_select_best_branch(uint32_t plan_id);

/**
 * omega_expand_scenario_tree - расширить дерево сценариев на один уровень
 * 
 * Генерирует новые ветви для всех листовых узлов
 */
int omega_expand_scenario_tree(uint32_t plan_id);

/**
 * omega_simulate_plan_execution - симулировать выполнение плана
 * 
 * Пройти по лучшей траектории и собрать прогнозы
 */
int omega_simulate_plan_execution(uint32_t plan_id,
                                 omega_plan_trajectory_t* trajectory_out);

/**
 * omega_get_planning_statistics - получить статистику
 */
const omega_planning_stats_t* omega_get_planning_statistics(void);

/**
 * omega_scenario_planner_shutdown - остановка
 */
void omega_scenario_planner_shutdown(void);

#endif  // OMEGA_SCENARIO_PLANNER_H
