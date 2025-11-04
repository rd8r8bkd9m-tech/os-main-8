#ifndef OMEGA_HIERARCHICAL_ABSTRACTION_H
#define OMEGA_HIERARCHICAL_ABSTRACTION_H

#include <stdint.h>
#include <stddef.h>

/**
 * Hierarchical Abstraction Header - Phase 4 Component
 * 
 * Преобразует 3+ шаговые паттерны в мета-события, создавая многоуровневую
 * иерархию абстракции. Это позволяет системе рассуждать о высокоуровневых
 * процессах как о атомарных единицах.
 */

#define OMEGA_MAX_META_EVENTS 100
#define OMEGA_ABSTRACTION_LEVELS 5  /* Уровни абстракции */

/**
 * omega_meta_event_t - мета-событие, созданное из паттерна
 * 
 * Представляет 3-шаговый паттерн как единое высокоуровневое событие.
 */
typedef struct {
    uint64_t meta_event_id;          /* Уникальный ID мета-события */
    uint64_t source_pattern_id;      /* ID исходного 3-шагового паттерна */
    
    uint64_t step_formula_ids[3];    /* IDs трех шагов паттерна */
    double confidence;               /* Уверенность мета-события */
    
    int64_t start_timestamp;         /* Когда началось */
    int64_t duration_ms;             /* Сколько длилось */
    
    int abstraction_level;           /* Уровень абстракции (0-4) */
    uint32_t metadata_flags;         /* Флаги для классификации */
} omega_meta_event_t;

/**
 * omega_abstraction_hierarchy_t - иерархия уровней абстракции
 * 
 * Организует события по уровням: факты → 3-шаги → мета-события → супер-мета → ...
 */
typedef struct {
    int level;                       /* Текущий уровень (0 = факты) */
    int event_count;                 /* Количество событий на этом уровне */
    uint64_t event_ids[OMEGA_MAX_META_EVENTS];  /* IDs событий */
    double avg_confidence;           /* Средняя уверенность на уровне */
} omega_abstraction_hierarchy_t;

/**
 * omega_hierarchical_stats_t - статистика иерархии
 */
typedef struct {
    int total_levels;                /* Всего уровней абстракции */
    int meta_events_created;         /* Количество созданных мета-событий */
    double average_abstraction_confidence;  /* Средняя уверенность */
    int patterns_abstracted;         /* Паттернов преобразовано в мета-события */
} omega_hierarchical_stats_t;

/* API функции */

/**
 * omega_hierarchical_abstraction_init - инициализация иерархии
 * 
 * Return: 0 при успехе, -1 при ошибке
 */
int omega_hierarchical_abstraction_init(void);

/**
 * omega_create_meta_event_from_pattern - превращение паттерна в мета-событие
 * 
 * Трансформирует 3-шаговый паттерн в высокоуровневое мета-событие.
 * 
 * @pattern_id: ID 3-шагового паттерна
 * @step_ids: массив из 3 formula IDs
 * @confidence: уверенность исходного паттерна
 * @start_time: начальная метка времени
 * @meta_event_out: выходная структура
 * 
 * Return: 0 при успехе, -1 при ошибке
 */
int omega_create_meta_event_from_pattern(uint64_t pattern_id, 
                                         const uint64_t* step_ids,
                                         double confidence,
                                         int64_t start_time,
                                         omega_meta_event_t* meta_event_out);

/**
 * omega_build_abstraction_hierarchy - построение иерархии уровней
 * 
 * Берет набор 3-шаговых паттернов и создает иерархию абстракции,
 * группируя мета-события по типам и связанности.
 * 
 * @meta_events: массив мета-событий
 * @event_count: количество мета-событий
 * @hierarchy_out: выходная иерархия
 * 
 * Return: количество уровней в иерархии
 */
int omega_build_abstraction_hierarchy(const omega_meta_event_t* meta_events,
                                      int event_count,
                                      omega_abstraction_hierarchy_t* hierarchy_out);

/**
 * omega_abstract_pattern_sequence - абстрактирование последовательности
 * 
 * Берет 3-4+ мета-события, которые происходят последовательно,
 * и создает мета-мета-событие (следующий уровень абстракции).
 * 
 * @meta_events: массив мета-событий
 * @event_count: количество мета-событий (обычно 3-4)
 * @merged_meta_event_out: выходное мета-мета-событие
 * 
 * Return: 0 при успехе, -1 при ошибке
 */
int omega_abstract_pattern_sequence(const omega_meta_event_t* meta_events,
                                    int event_count,
                                    omega_meta_event_t* merged_meta_event_out);

/**
 * omega_get_hierarchy_level_by_event - получить уровень события в иерархии
 * 
 * @event_id: ID события (pattern или meta_event)
 * 
 * Return: уровень абстракции (0 для фактов, 1 для 3-шагов, 2+ для мета)
 */
int omega_get_hierarchy_level_by_event(uint64_t event_id);

/**
 * omega_compress_representation - сжатие представления
 * 
 * Заменяет длинную последовательность низкоуровневых событий
 * эквивалентным мета-событием высокого уровня.
 * 
 * Пример: [fact_A, fact_B, fact_C, fact_D, fact_E, fact_F]
 *         → [MetaEvent_1, MetaEvent_2]
 * 
 * Return: количество созданных мета-событий
 */
int omega_compress_representation(void);

/**
 * omega_get_hierarchical_statistics - получить статистику иерархии
 * 
 * Return: const указатель на статистику
 */
const omega_hierarchical_stats_t* omega_get_hierarchical_statistics(void);

/**
 * omega_hierarchical_abstraction_shutdown - остановка
 */
void omega_hierarchical_abstraction_shutdown(void);

#endif // OMEGA_HIERARCHICAL_ABSTRACTION_H
