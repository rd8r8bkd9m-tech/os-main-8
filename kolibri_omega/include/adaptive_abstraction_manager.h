/**
 * adaptive_abstraction_manager.h - Phase 7: Adaptive Abstraction Levels
 *
 * Динамическое управление уровнями абстракции на основе метрик расхождения,
 * сложности и производительности. Система автоматически повышает или понижает
 * детальность представления в зависимости от текущей ситуации.
 */

#ifndef OMEGA_ADAPTIVE_ABSTRACTION_MANAGER_H
#define OMEGA_ADAPTIVE_ABSTRACTION_MANAGER_H

#include <stdint.h>

/* ========== Определения констант ========== */

#define OMEGA_MAX_ABSTRACTION_LEVELS 8
#define OMEGA_MAX_ADAPTIVE_RULES 32
#define OMEGA_MAX_ABSTRACTION_METRICS 64

/* ========== Типы абстракции ========== */

typedef enum {
    OMEGA_LEVEL_MICROSECOND = 0,    // Все детали, каждый такт
    OMEGA_LEVEL_MILLISECOND = 1,    // ~100 тактов агрегированы
    OMEGA_LEVEL_DECISECOND = 2,     // ~1000 тактов
    OMEGA_LEVEL_SECOND = 3,         // ~10k тактов
    OMEGA_LEVEL_MINUTE = 4,         // Долгосрочные тренды
    OMEGA_LEVEL_HOUR = 5,           // Очень высокий уровень
    OMEGA_LEVEL_DAY = 6,            // Стратегический уровень
    OMEGA_LEVEL_MONTH = 7           // Максимальная абстракция
} omega_abstraction_level_t;

/* ========== Типы метрик ========== */

typedef enum {
    OMEGA_METRIC_DIVERGENCE = 0,      // Расхождение от базовой линии
    OMEGA_METRIC_COMPLEXITY = 1,      // Сложность (количество формул)
    OMEGA_METRIC_SYNCHRONIZATION = 2, // Синхронизация агентов
    OMEGA_METRIC_PATTERN_DENSITY = 3, // Плотность паттернов
    OMEGA_METRIC_CAUSALITY_DEPTH = 4, // Глубина причинных цепей
    OMEGA_METRIC_MEMORY_USAGE = 5,    // Использование памяти
    OMEGA_METRIC_LATENCY = 6          // Время на цикл
} omega_metric_type_t;

/* ========== Структуры данных ========== */

/**
 * omega_abstraction_metric_t - Метрика для адаптации
 */
typedef struct {
    omega_metric_type_t metric_type;
    double current_value;
    double threshold_low;   // Нижний порог для повышения детальности
    double threshold_high;  // Верхний порог для понижения детальности
    double weight;          // Вес метрики в решении (0.0-1.0)
} omega_abstraction_metric_t;

/**
 * omega_adaptive_rule_t - Правило адаптации
 */
typedef struct {
    uint64_t rule_id;
    omega_metric_type_t trigger_metric;
    double trigger_value;
    omega_abstraction_level_t target_level;
    char description[128];
    int is_active;
} omega_adaptive_rule_t;

/**
 * omega_abstraction_level_config_t - Конфигурация уровня абстракции
 */
typedef struct {
    omega_abstraction_level_t level;
    char level_name[32];
    
    // Параметры этого уровня
    int aggregation_window;      // Сколько тактов агрегировать
    int formula_compression_ratio; // Во сколько раз сжимать формулы
    int keep_top_n_patterns;     // Сохранять только top-N паттернов
    double pattern_confidence_threshold; // Минимальная уверенность
    
    // Метрики производительности
    int estimated_memory_kb;
    double estimated_latency_ms;
} omega_abstraction_level_config_t;

/**
 * omega_adaptation_context_t - Контекст адаптации
 */
typedef struct {
    omega_abstraction_level_t current_level;
    omega_abstraction_level_t target_level;
    
    omega_abstraction_metric_t metrics[OMEGA_MAX_ABSTRACTION_METRICS];
    int metric_count;
    
    omega_adaptive_rule_t rules[OMEGA_MAX_ADAPTIVE_RULES];
    int rule_count;
    
    // История адаптаций
    int adaptation_count;
    int last_adaptation_timestamp;
    
    // Статистика
    double average_level;  // Среднее значение уровня абстракции
    int level_changes;     // Количество изменений уровня
} omega_adaptation_context_t;

/**
 * omega_adaptive_abstraction_stats_t - Статистика адаптации
 */
typedef struct {
    int total_adaptations;
    int upward_adaptations;   // К более низкому уровню детали
    int downward_adaptations; // К более высокому уровню абстракции
    
    double average_level_used;
    omega_abstraction_level_t most_used_level;
    
    double memory_savings_percent;
    double latency_reduction_percent;
    
    int rules_triggered;
    int rules_overridden;
} omega_adaptive_abstraction_stats_t;

/* ========== API функции ========== */

/**
 * omega_adaptive_abstraction_init - инициализация
 */
int omega_adaptive_abstraction_init(void);

/**
 * omega_register_abstraction_metric - зарегистрировать метрику
 */
int omega_register_abstraction_metric(omega_metric_type_t metric_type,
                                     double threshold_low,
                                     double threshold_high,
                                     double weight);

/**
 * omega_add_adaptation_rule - добавить правило адаптации
 * 
 * Правило автоматически переводит систему на другой уровень абстракции
 * когда метрика превышает триггерное значение.
 */
int omega_add_adaptation_rule(omega_metric_type_t trigger_metric,
                             double trigger_value,
                             omega_abstraction_level_t target_level,
                             const char* description);

/**
 * omega_compute_adaptation_level - вычислить оптимальный уровень абстракции
 * 
 * На основе текущих метрик вычисляет, какой уровень абстракции выбрать.
 * @return Рекомендуемый уровень абстракции
 */
omega_abstraction_level_t omega_compute_adaptation_level(void);

/**
 * omega_update_metric - обновить значение метрики
 */
int omega_update_metric(omega_metric_type_t metric_type, double value);

/**
 * omega_apply_adaptation - применить адаптацию
 * 
 * Переводит систему на новый уровень абстракции с сохранением критической информации.
 * @return 1 если адаптация произошла, 0 если уровень не изменился
 */
int omega_apply_adaptation(omega_abstraction_level_t new_level);

/**
 * omega_get_current_abstraction_level - получить текущий уровень
 */
omega_abstraction_level_t omega_get_current_abstraction_level(void);

/**
 * omega_get_level_config - получить конфигурацию уровня
 */
const omega_abstraction_level_config_t* omega_get_level_config(omega_abstraction_level_t level);

/**
 * omega_get_adaptive_abstraction_statistics - получить статистику
 */
const omega_adaptive_abstraction_stats_t* omega_get_adaptive_abstraction_statistics(void);

/**
 * omega_adaptive_abstraction_shutdown - остановка
 */
void omega_adaptive_abstraction_shutdown(void);

#endif // OMEGA_ADAPTIVE_ABSTRACTION_MANAGER_H
