#include "kolibri_omega/include/hierarchical_abstraction.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define OMEGA_MAX_META_EVENTS_INTERNAL 100

typedef struct {
    omega_meta_event_t events[OMEGA_MAX_META_EVENTS_INTERNAL];
    int event_count;
    
    omega_abstraction_hierarchy_t hierarchies[OMEGA_ABSTRACTION_LEVELS];
    int hierarchy_count;
    
    omega_hierarchical_stats_t stats;
} omega_hierarchical_ctx_t;

static omega_hierarchical_ctx_t hierarchy_ctx = {0};

/**
 * omega_hierarchical_abstraction_init - инициализация
 */
int omega_hierarchical_abstraction_init(void) {
    memset(&hierarchy_ctx, 0, sizeof(hierarchy_ctx));
    hierarchy_ctx.stats.total_levels = OMEGA_ABSTRACTION_LEVELS;
    
    printf("[HierarchicalAbstraction] Initialized with %d levels\n",
           OMEGA_ABSTRACTION_LEVELS);
    
    return 0;
}

/**
 * omega_create_meta_event_from_pattern - создание мета-события
 */
int omega_create_meta_event_from_pattern(uint64_t pattern_id, 
                                         const uint64_t* step_ids,
                                         double confidence,
                                         int64_t start_time,
                                         omega_meta_event_t* meta_event_out) {
    if (!step_ids || !meta_event_out) {
        return -1;
    }
    
    if (hierarchy_ctx.event_count >= OMEGA_MAX_META_EVENTS_INTERNAL) {
        return -1;  // Переполнение
    }
    
    meta_event_out->meta_event_id = 5000 + hierarchy_ctx.event_count;
    meta_event_out->source_pattern_id = pattern_id;
    
    meta_event_out->step_formula_ids[0] = step_ids[0];
    meta_event_out->step_formula_ids[1] = step_ids[1];
    meta_event_out->step_formula_ids[2] = step_ids[2];
    
    meta_event_out->confidence = confidence;
    meta_event_out->start_timestamp = start_time;
    meta_event_out->duration_ms = 50;  // Типичная длительность 3-шагового паттерна
    
    meta_event_out->abstraction_level = 1;  // Уровень 1 = 3-шаговые паттерны
    meta_event_out->metadata_flags = 0;
    
    // Добавляем в контекст
    memcpy(&hierarchy_ctx.events[hierarchy_ctx.event_count],
           meta_event_out, sizeof(omega_meta_event_t));
    hierarchy_ctx.event_count++;
    hierarchy_ctx.stats.meta_events_created++;
    hierarchy_ctx.stats.patterns_abstracted++;
    
    printf("[HierarchicalAbstraction] Created meta_event %lu from pattern %lu "
           "(%lu → %lu → %lu, confidence: %.3f)\n",
           (unsigned long)meta_event_out->meta_event_id, (unsigned long)pattern_id,
           (unsigned long)step_ids[0], (unsigned long)step_ids[1], (unsigned long)step_ids[2], confidence);
    
    return 0;
}

/**
 * omega_build_abstraction_hierarchy - построение иерархии
 */
int omega_build_abstraction_hierarchy(const omega_meta_event_t* meta_events,
                                      int event_count,
                                      omega_abstraction_hierarchy_t* hierarchy_out) {
    if (!meta_events || !hierarchy_out || event_count == 0) {
        return 0;
    }
    
    // Создаем нулевую иерархию (факты)
    hierarchy_out[0].level = 0;
    hierarchy_out[0].event_count = 0;
    hierarchy_out[0].avg_confidence = 1.0;
    
    // Создаем первую иерархию (3-шаговые паттерны)
    hierarchy_out[1].level = 1;
    hierarchy_out[1].event_count = event_count;
    
    double sum_conf = 0.0;
    for (int i = 0; i < event_count && i < OMEGA_MAX_META_EVENTS; i++) {
        hierarchy_out[1].event_ids[i] = meta_events[i].meta_event_id;
        sum_conf += meta_events[i].confidence;
    }
    hierarchy_out[1].avg_confidence = sum_conf / event_count;
    
    printf("[HierarchicalAbstraction] Built hierarchy with level 0 (facts) "
           "and level 1 (%d meta_events, avg_confidence: %.3f)\n",
           event_count, hierarchy_out[1].avg_confidence);
    
    return 2;  // Количество уровней
}

/**
 * omega_abstract_pattern_sequence - абстрактирование последовательности
 */
int omega_abstract_pattern_sequence(const omega_meta_event_t* meta_events,
                                    int event_count,
                                    omega_meta_event_t* merged_meta_event_out) {
    if (!meta_events || !merged_meta_event_out || event_count < 2) {
        return -1;
    }
    
    // Создаем мета-мета-событие из последовательности мета-событий
    merged_meta_event_out->meta_event_id = 6000 + hierarchy_ctx.event_count;
    merged_meta_event_out->abstraction_level = 2;  // Уровень 2
    
    // Копируем первые 3 formula ID из первого события
    merged_meta_event_out->step_formula_ids[0] = meta_events[0].step_formula_ids[0];
    merged_meta_event_out->step_formula_ids[1] = meta_events[0].step_formula_ids[1];
    merged_meta_event_out->step_formula_ids[2] = meta_events[0].step_formula_ids[2];
    
    // Общая уверенность - произведение
    double combined_conf = 1.0;
    for (int i = 0; i < event_count; i++) {
        combined_conf *= meta_events[i].confidence;
    }
    merged_meta_event_out->confidence = combined_conf;
    
    // Временные данные
    merged_meta_event_out->start_timestamp = meta_events[0].start_timestamp;
    if (event_count > 0) {
        merged_meta_event_out->duration_ms = 
            (meta_events[event_count - 1].start_timestamp + 50) - 
            meta_events[0].start_timestamp;
    }
    
    printf("[HierarchicalAbstraction] Abstracted sequence of %d meta_events into "
           "meta_meta_event %lu (confidence: %.4f)\n",
           event_count, (unsigned long)merged_meta_event_out->meta_event_id,
           merged_meta_event_out->confidence);
    
    return 0;
}

/**
 * omega_get_hierarchy_level_by_event - получить уровень события
 */
int omega_get_hierarchy_level_by_event(uint64_t event_id) {
    // Диапазоны ID событий:
    // 0-999: факты (уровень 0)
    // 1000-4999: 2-шаговые правила (базовый уровень)
    // 5000-5999: 3-шаговые мета-события (уровень 1)
    // 6000-6999: мета-мета-события (уровень 2)
    
    if (event_id >= 6000) return 2;
    if (event_id >= 5000) return 1;
    if (event_id >= 1000) return 0;
    return 0;  // Факты
}

/**
 * omega_compress_representation - сжатие представления
 */
int omega_compress_representation(void) {
    // Берем все накопленные события и пытаемся их сжать
    if (hierarchy_ctx.event_count < 3) {
        return 0;
    }
    
    // Простой алгоритм: последовательные мета-события объединяем
    int compressed = 0;
    for (int i = 0; i < hierarchy_ctx.event_count - 2; i++) {
        if (hierarchy_ctx.events[i].abstraction_level == 1 &&
            hierarchy_ctx.events[i+1].abstraction_level == 1) {
            
            // Проверяем временную близость
            int64_t gap = hierarchy_ctx.events[i+1].start_timestamp - 
                         (hierarchy_ctx.events[i].start_timestamp + 
                          hierarchy_ctx.events[i].duration_ms);
            
            if (gap < 100) {  // Менее чем 100ms между ними
                omega_meta_event_t merged;
                omega_abstract_pattern_sequence(
                    &hierarchy_ctx.events[i], 2, &merged
                );
                compressed++;
            }
        }
    }
    
    printf("[HierarchicalAbstraction] Compressed %d sequential events\n",
           compressed);
    
    return compressed;
}

/**
 * omega_get_hierarchical_statistics - получить статистику
 */
const omega_hierarchical_stats_t* omega_get_hierarchical_statistics(void) {
    hierarchy_ctx.stats.total_levels = OMEGA_ABSTRACTION_LEVELS;
    hierarchy_ctx.stats.meta_events_created = hierarchy_ctx.event_count;
    
    if (hierarchy_ctx.event_count > 0) {
        double sum = 0.0;
        for (int i = 0; i < hierarchy_ctx.event_count; i++) {
            sum += hierarchy_ctx.events[i].confidence;
        }
        hierarchy_ctx.stats.average_abstraction_confidence = 
            sum / hierarchy_ctx.event_count;
    }
    
    return &hierarchy_ctx.stats;
}

/**
 * omega_hierarchical_abstraction_shutdown - остановка
 */
void omega_hierarchical_abstraction_shutdown(void) {
    printf("[HierarchicalAbstraction] Shutdown: processed %d meta_events, "
           "abstracted %d patterns\n",
           hierarchy_ctx.event_count, 
           hierarchy_ctx.stats.patterns_abstracted);
    memset(&hierarchy_ctx, 0, sizeof(hierarchy_ctx));
}
