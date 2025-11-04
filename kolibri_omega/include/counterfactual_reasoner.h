/**
 * counterfactual_reasoner.h - Phase 6: Counterfactual Reasoning
 *
 * Модуль для анализа гипотетических сценариев ("что если").
 * Позволяет создавать альтернативные версии текущего состояния,
 * применять гипотетические вмешательства и анализировать причинно-следственные связи.
 */

#ifndef OMEGA_COUNTERFACTUAL_REASONER_H
#define OMEGA_COUNTERFACTUAL_REASONER_H

#include <stdint.h>
#include <stddef.h>

/* ========== Определения констант ========== */

#define OMEGA_MAX_SCENARIOS 20           // Максимум параллельных сценариев
#define OMEGA_MAX_INTERVENTIONS 50       // Максимум вмешательств на сценарий
#define OMEGA_MAX_CAUSAL_LINKS 100       // Максимум причинно-следственных связей
#define OMEGA_MAX_BRANCHES 200           // Максимум ветвей дерева сценариев
#define OMEGA_SCENARIO_NAME_LEN 64       // Длина имени сценария

/* ========== Типы вмешательств ========== */

typedef enum {
    OMEGA_INTERVENTION_DISABLE_AGENT = 0,    // Отключить агента
    OMEGA_INTERVENTION_FORCE_ACTION = 1,     // Принудительное действие
    OMEGA_INTERVENTION_MODIFY_PARAMETER = 2, // Изменить параметр
    OMEGA_INTERVENTION_BLOCK_EVENT = 3,      // Заблокировать событие
    OMEGA_INTERVENTION_INJECT_KNOWLEDGE = 4  // Добавить знание
} omega_intervention_type_t;

/* ========== Типы причинности ========== */

typedef enum {
    OMEGA_CAUSALITY_DIRECT = 0,       // Прямая причина
    OMEGA_CAUSALITY_INDIRECT = 1,     // Косвенная причина
    OMEGA_CAUSALITY_CONDITIONAL = 2,  // Условная причина
    OMEGA_CAUSALITY_CORRELATION = 3   // Корреляция (не причина)
} omega_causality_type_t;

/* ========== Структуры данных ========== */

/**
 * omega_intervention_t - Гипотетическое вмешательство
 */
typedef struct {
    uint64_t intervention_id;                    // Уникальный ID
    omega_intervention_type_t intervention_type; // Тип вмешательства
    uint32_t target_agent_id;                    // Целевой агент (если применимо)
    uint64_t target_formula_id;                  // Целевая формула
    double intervention_strength;                // Сила вмешательства (0.0-1.0)
    int64_t apply_at_timestamp;                  // Когда применить
    char description[128];                       // Описание вмешательства
} omega_intervention_t;

/**
 * omega_causal_link_t - Причинно-следственная связь
 */
typedef struct {
    uint64_t link_id;
    uint64_t cause_formula_id;           // Формула-причина
    uint64_t effect_formula_id;          // Формула-следствие
    omega_causality_type_t causality_type;
    double strength;                      // Сила связи (0.0-1.0)
    int64_t observed_delay_ms;           // Задержка между причиной и следствием
    int confirmed;                        // 1 если подтверждена, 0 если гипотеза
} omega_causal_link_t;

/**
 * omega_scenario_t - Гипотетический сценарий
 */
typedef struct {
    uint64_t scenario_id;                              // Уникальный ID сценария
    char scenario_name[OMEGA_SCENARIO_NAME_LEN];       // Название сценария
    int64_t divergence_timestamp;                      // Когда сценарий отходит от базовой линии
    
    omega_intervention_t interventions[OMEGA_MAX_INTERVENTIONS];
    int intervention_count;
    
    // Ожидаемые исходы
    double expected_canvas_items;  // Ожидаемое количество элементов на холсте
    double expected_agent_sync;    // Ожидаемая синхронизация агентов
    double expected_pattern_count; // Ожидаемое количество паттернов
    
    // Реальные результаты (заполняются при симуляции)
    double actual_canvas_items;
    double actual_agent_sync;
    double actual_pattern_count;
    
    // Статистика
    double divergence_ratio;       // Насколько результат отличается от ожидаемого
    int outcome_consistent;        // 1 если результат совпадает с ожиданием
    
    int is_active;                 // 1 если сценарий активен
} omega_scenario_t;

/**
 * omega_branch_t - Ветвь дерева сценариев
 */
typedef struct {
    uint64_t branch_id;
    uint64_t parent_scenario_id;        // Сценарий-родитель (0 если корень)
    uint64_t scenario_id;               // Ассоциированный сценарий
    
    int depth;                          // Глубина в дереве (0 = корень)
    int num_children;                   // Количество дочерних ветвей
    uint64_t child_branch_ids[5];       // IDs дочерних ветвей
    
    double branch_probability;          // Вероятность этой ветви (0.0-1.0)
    double cumulative_impact;           // Совокупный импакт вмешательств
} omega_branch_t;

/**
 * omega_counterfactual_stats_t - Статистика counterfactual анализа
 */
typedef struct {
    int total_scenarios;
    int active_scenarios;
    int scenarios_completed;
    
    int total_interventions_tested;
    int high_impact_interventions;  // Вмешательства с impact > 0.7
    
    int causal_links_discovered;
    int causal_links_confirmed;
    
    int branches_explored;
    double max_branch_probability;
    
    double average_divergence;
    double largest_divergence;
} omega_counterfactual_stats_t;

/* ========== API функции ========== */

/**
 * omega_counterfactual_reasoner_init - инициализация
 */
int omega_counterfactual_reasoner_init(void);

/**
 * omega_create_scenario - создать новый сценарий
 * 
 * @param scenario_name - название сценария
 * @param divergence_timestamp - момент отхода от базовой линии
 * @return ID созданного сценария или 0 при ошибке
 */
uint64_t omega_create_scenario(const char* scenario_name, int64_t divergence_timestamp);

/**
 * omega_add_intervention - добавить вмешательство в сценарий
 */
int omega_add_intervention(uint64_t scenario_id, omega_intervention_type_t type,
                          uint32_t target_agent_id, uint64_t target_formula_id,
                          double strength, const char* description);

/**
 * omega_analyze_scenario_branch - проанализировать ветвь дерева сценариев
 * 
 * Создает новую ветвь и вычисляет вероятность исхода.
 * @return ID созданной ветви
 */
uint64_t omega_analyze_scenario_branch(uint64_t parent_scenario_id, int depth);

/**
 * omega_apply_interventions - применить все вмешательства сценария
 * 
 * Симулирует эффекты вмешательств (без изменения реального состояния).
 * @return 1 если успешно, -1 при ошибке
 */
int omega_apply_interventions(uint64_t scenario_id);

/**
 * omega_detect_causal_links - обнаружить причинно-следственные связи
 * 
 * Анализирует последовательности формул в сценарии и находит причинные связи.
 * @return Количество обнаруженных связей
 */
int omega_detect_causal_links(uint64_t scenario_id);

/**
 * omega_compute_divergence - вычислить расхождение от базовой линии
 * 
 * Сравнивает ожидаемые и фактические результаты.
 * @return Ratio расхождения (0.0 = идентично, 1.0 = полное различие)
 */
double omega_compute_divergence(uint64_t scenario_id);

/**
 * omega_rank_scenarios_by_impact - ранжировать сценарии по влиянию
 * 
 * Заполняет массив отсортированных ID сценариев.
 * @param scenario_ids_out - выходной массив (макс OMEGA_MAX_SCENARIOS)
 * @param max_count - размер выходного массива
 * @return Количество заполненных элементов
 */
int omega_rank_scenarios_by_impact(uint64_t* scenario_ids_out, int max_count);

/**
 * omega_get_counterfactual_statistics - получить статистику
 */
const omega_counterfactual_stats_t* omega_get_counterfactual_statistics(void);

/**
 * omega_counterfactual_reasoner_shutdown - остановка
 */
void omega_counterfactual_reasoner_shutdown(void);

#endif // OMEGA_COUNTERFACTUAL_REASONER_H
