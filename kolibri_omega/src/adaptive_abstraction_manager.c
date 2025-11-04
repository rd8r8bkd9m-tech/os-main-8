#include "kolibri_omega/include/adaptive_abstraction_manager.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

typedef struct {
    omega_abstraction_level_config_t level_configs[OMEGA_MAX_ABSTRACTION_LEVELS];
    omega_adaptation_context_t adaptation_ctx;
    omega_adaptive_abstraction_stats_t stats;
} omega_adaptive_ctx_t;

static omega_adaptive_ctx_t adaptive_ctx = {0};

/**
 * omega_adaptive_abstraction_init - инициализация
 */
int omega_adaptive_abstraction_init(void) {
    memset(&adaptive_ctx, 0, sizeof(adaptive_ctx));
    
    // Инициализируем конфигурации для каждого уровня
    const char* level_names[] = {
        "Microsecond", "Millisecond", "Decisecond", "Second",
        "Minute", "Hour", "Day", "Month"
    };
    
    int aggregation_windows[] = {1, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000};
    int memory_estimates[] = {60, 50, 40, 30, 20, 15, 10, 8};
    double latency_estimates[] = {15.0, 10.0, 8.0, 6.0, 4.0, 3.0, 2.0, 1.5};
    
    for (int i = 0; i < OMEGA_MAX_ABSTRACTION_LEVELS; i++) {
        adaptive_ctx.level_configs[i].level = i;
        strncpy(adaptive_ctx.level_configs[i].level_name, level_names[i], 31);
        adaptive_ctx.level_configs[i].aggregation_window = aggregation_windows[i];
        adaptive_ctx.level_configs[i].formula_compression_ratio = 1 + i;
        adaptive_ctx.level_configs[i].keep_top_n_patterns = 50 - (i * 5);
        adaptive_ctx.level_configs[i].pattern_confidence_threshold = 0.5 + (i * 0.05);
        adaptive_ctx.level_configs[i].estimated_memory_kb = memory_estimates[i];
        adaptive_ctx.level_configs[i].estimated_latency_ms = latency_estimates[i];
    }
    
    adaptive_ctx.adaptation_ctx.current_level = OMEGA_LEVEL_MILLISECOND;
    adaptive_ctx.adaptation_ctx.target_level = OMEGA_LEVEL_MILLISECOND;
    
    printf("[AdaptiveAbstraction] Initialized with %d abstraction levels\n",
           OMEGA_MAX_ABSTRACTION_LEVELS);
    
    return 0;
}

/**
 * omega_register_abstraction_metric - зарегистрировать метрику
 */
int omega_register_abstraction_metric(omega_metric_type_t metric_type,
                                     double threshold_low,
                                     double threshold_high,
                                     double weight) {
    if (adaptive_ctx.adaptation_ctx.metric_count >= OMEGA_MAX_ABSTRACTION_METRICS) {
        return -1;
    }
    
    omega_abstraction_metric_t* metric = &adaptive_ctx.adaptation_ctx.metrics[
        adaptive_ctx.adaptation_ctx.metric_count];
    
    metric->metric_type = metric_type;
    metric->threshold_low = threshold_low;
    metric->threshold_high = threshold_high;
    metric->weight = weight;
    metric->current_value = 0.0;
    
    adaptive_ctx.adaptation_ctx.metric_count++;
    
    printf("[AdaptiveAbstraction] Registered metric %d (thresholds: %.2f-%.2f, weight: %.2f)\n",
           metric_type, threshold_low, threshold_high, weight);
    
    return 0;
}

/**
 * omega_add_adaptation_rule - добавить правило адаптации
 */
int omega_add_adaptation_rule(omega_metric_type_t trigger_metric,
                             double trigger_value,
                             omega_abstraction_level_t target_level,
                             const char* description) {
    if (adaptive_ctx.adaptation_ctx.rule_count >= OMEGA_MAX_ADAPTIVE_RULES) {
        return -1;
    }
    
    omega_adaptive_rule_t* rule = &adaptive_ctx.adaptation_ctx.rules[
        adaptive_ctx.adaptation_ctx.rule_count];
    
    rule->rule_id = 9000 + adaptive_ctx.adaptation_ctx.rule_count;
    rule->trigger_metric = trigger_metric;
    rule->trigger_value = trigger_value;
    rule->target_level = target_level;
    strncpy(rule->description, description, sizeof(rule->description) - 1);
    rule->is_active = 1;
    
    adaptive_ctx.adaptation_ctx.rule_count++;
    
    printf("[AdaptiveAbstraction] Added rule: %s -> Level %d\n", description, target_level);
    
    return 0;
}

/**
 * omega_compute_adaptation_level - вычислить оптимальный уровень
 */
omega_abstraction_level_t omega_compute_adaptation_level(void) {
    // Вычисляем взвешенный скор для каждого уровня
    double scores[OMEGA_MAX_ABSTRACTION_LEVELS] = {0};
    
    // Проверяем каждую метрику
    for (int m = 0; m < adaptive_ctx.adaptation_ctx.metric_count; m++) {
        omega_abstraction_metric_t* metric = &adaptive_ctx.adaptation_ctx.metrics[m];
        
        // Если метрика выше верхнего порога → переходим на более высокую абстракцию
        if (metric->current_value > metric->threshold_high) {
            for (int l = OMEGA_LEVEL_DECISECOND; l <= OMEGA_LEVEL_MONTH; l++) {
                scores[l] += metric->weight;
            }
        }
        // Если метрика ниже нижнего порога → переходим на более низкую абстракцию
        else if (metric->current_value < metric->threshold_low) {
            for (int l = OMEGA_LEVEL_MICROSECOND; l <= OMEGA_LEVEL_MILLISECOND; l++) {
                scores[l] += metric->weight;
            }
        }
    }
    
    // Выбираем уровень с максимальным скором
    // Используем threshold: требуем явное улучшение для смены уровня
    int best_level = adaptive_ctx.adaptation_ctx.current_level;
    double best_score = scores[best_level] - 0.01;  // Небольшой penalty за смену
    
    for (int l = 0; l < OMEGA_MAX_ABSTRACTION_LEVELS; l++) {
        if (scores[l] > best_score) {
            best_score = scores[l];
            best_level = l;
        }
    }
    
    return (omega_abstraction_level_t)best_level;
}

/**
 * omega_update_metric - обновить метрику
 */
int omega_update_metric(omega_metric_type_t metric_type, double value) {
    for (int i = 0; i < adaptive_ctx.adaptation_ctx.metric_count; i++) {
        if (adaptive_ctx.adaptation_ctx.metrics[i].metric_type == metric_type) {
            adaptive_ctx.adaptation_ctx.metrics[i].current_value = value;
            return 0;
        }
    }
    return -1;  // Метрика не зарегистрирована
}

/**
 * omega_apply_adaptation - применить адаптацию
 */
int omega_apply_adaptation(omega_abstraction_level_t new_level) {
    if (new_level == adaptive_ctx.adaptation_ctx.current_level) {
        return 0;  // Уровень не изменился
    }
    
    omega_abstraction_level_config_t* old_config = 
        &adaptive_ctx.level_configs[adaptive_ctx.adaptation_ctx.current_level];
    omega_abstraction_level_config_t* new_config = 
        &adaptive_ctx.level_configs[new_level];
    
    printf("[AdaptiveAbstraction] Adapting: %s -> %s\n",
           old_config->level_name, new_config->level_name);
    printf("  Memory: %d KB -> %d KB, Latency: %.1f ms -> %.1f ms\n",
           old_config->estimated_memory_kb, new_config->estimated_memory_kb,
           old_config->estimated_latency_ms, new_config->estimated_latency_ms);
    
    // Сохраняем предыдущий уровень
    int old_level_int = adaptive_ctx.adaptation_ctx.current_level;
    
    // Применяем новый уровень
    adaptive_ctx.adaptation_ctx.current_level = new_level;
    adaptive_ctx.adaptation_ctx.last_adaptation_timestamp = 0;
    adaptive_ctx.adaptation_ctx.adaptation_count++;
    adaptive_ctx.stats.total_adaptations++;
    
    // Статистика
    if (new_level > old_level_int) {
        adaptive_ctx.stats.downward_adaptations++;  // К более высокой абстракции
    } else {
        adaptive_ctx.stats.upward_adaptations++;   // К более низкой абстракции
    }
    
    return 1;
}

/**
 * omega_get_current_abstraction_level - получить текущий уровень
 */
omega_abstraction_level_t omega_get_current_abstraction_level(void) {
    return adaptive_ctx.adaptation_ctx.current_level;
}

/**
 * omega_get_level_config - получить конфигурацию уровня
 */
const omega_abstraction_level_config_t* omega_get_level_config(omega_abstraction_level_t level) {
    if (level < OMEGA_MAX_ABSTRACTION_LEVELS) {
        return &adaptive_ctx.level_configs[level];
    }
    return NULL;
}

/**
 * omega_get_adaptive_abstraction_statistics - получить статистику
 */
const omega_adaptive_abstraction_stats_t* omega_get_adaptive_abstraction_statistics(void) {
    // Вычисляем средний уровень
    if (adaptive_ctx.stats.total_adaptations > 0) {
        adaptive_ctx.stats.average_level_used = 
            (adaptive_ctx.stats.upward_adaptations + adaptive_ctx.stats.downward_adaptations) / 2.0;
    }
    
    // Устанавливаем most_used_level
    adaptive_ctx.stats.most_used_level = adaptive_ctx.adaptation_ctx.current_level;
    
    // Оцениваем экономию ресурсов
    const omega_abstraction_level_config_t* min_config = &adaptive_ctx.level_configs[0];
    const omega_abstraction_level_config_t* cur_config = 
        &adaptive_ctx.level_configs[adaptive_ctx.adaptation_ctx.current_level];
    
    if (min_config->estimated_memory_kb > 0) {
        adaptive_ctx.stats.memory_savings_percent = 
            (100.0 * (min_config->estimated_memory_kb - cur_config->estimated_memory_kb)) / 
            min_config->estimated_memory_kb;
    }
    
    if (min_config->estimated_latency_ms > 0.001) {
        adaptive_ctx.stats.latency_reduction_percent = 
            (100.0 * (min_config->estimated_latency_ms - cur_config->estimated_latency_ms)) / 
            min_config->estimated_latency_ms;
    }
    
    return &adaptive_ctx.stats;
}

/**
 * omega_adaptive_abstraction_shutdown - остановка
 */
void omega_adaptive_abstraction_shutdown(void) {
    const omega_adaptive_abstraction_stats_t* stats = 
        omega_get_adaptive_abstraction_statistics();
    
    printf("[AdaptiveAbstraction] Shutdown: %d total adaptations\n",
           stats->total_adaptations);
    printf("  Upward (detail): %d, Downward (abstract): %d\n",
           stats->upward_adaptations, stats->downward_adaptations);
    printf("  Current level: %s\n", 
           adaptive_ctx.level_configs[adaptive_ctx.adaptation_ctx.current_level].level_name);
    printf("  Memory savings: %.1f%%, Latency reduction: %.1f%%\n",
           stats->memory_savings_percent, stats->latency_reduction_percent);
    
    memset(&adaptive_ctx, 0, sizeof(adaptive_ctx));
}
