#ifndef OMEGA_AGENT_COORDINATOR_H
#define OMEGA_AGENT_COORDINATOR_H

#include <stdint.h>
#include <stddef.h>

/**
 * Agent Coordinator Header - Phase 5 Component
 * 
 * Обнаруживает паттерны координации между несколькими объектами/агентами.
 * Отслеживает синхронизированные действия, emergent поведение и групповые паттерны.
 */

#define OMEGA_MAX_AGENTS 10
#define OMEGA_MAX_AGENT_PATTERNS 50
#define OMEGA_MAX_COORDINATION_HISTORY 100

/**
 * omega_agent_state_t - состояние одного агента в момент времени
 */
typedef struct {
    uint32_t agent_id;           /* ID агента */
    uint64_t formula_id;         /* Formula ID его состояния */
    int64_t timestamp;           /* Когда это произошло */
    double confidence;           /* Уверенность в этом состоянии */
} omega_agent_state_t;

/**
 * omega_coordination_event_t - событие координации между агентами
 * 
 * Представляет синхронизированные действия множества объектов.
 */
typedef struct {
    uint64_t coordination_id;           /* Уникальный ID события */
    uint32_t agent_ids[OMEGA_MAX_AGENTS];  /* IDs участвующих агентов */
    int agent_count;                    /* Сколько агентов участвует */
    
    int64_t start_timestamp;            /* Начало события */
    int64_t end_timestamp;              /* Конец события */
    
    double coordination_strength;       /* 0.0-1.0: насколько хорошо координировано */
    int coordination_type;              /* 0=sync, 1=async, 2=hierarchical */
    
    uint64_t pattern_confidence;        /* Уверенность в паттерне */
} omega_coordination_event_t;

/**
 * omega_agent_pattern_t - обнаруженный паттерн поведения агентов
 */
typedef struct {
    uint64_t pattern_id;                /* ID паттерна */
    uint32_t agent_ids[OMEGA_MAX_AGENTS];  /* Какие агенты участвуют */
    int agent_count;                    /* Количество агентов */
    
    double average_confidence;          /* Средняя уверенность */
    int occurrences;                    /* Сколько раз встречался */
    
    int pattern_type;                   /* 0=flocking, 1=avoidance, 2=pursuit, 3=other */
} omega_agent_pattern_t;

/**
 * omega_multi_agent_stats_t - статистика мульти-агентных паттернов
 */
typedef struct {
    int total_agents;                   /* Всего уникальных агентов */
    int total_coordination_events;      /* Событий координации */
    int total_patterns;                 /* Обнаруженных паттернов */
    
    double average_coordination_strength;  /* Средняя синхронность */
    int most_common_pattern_type;       /* Самый частый тип паттерна */
    
    int synchronization_pairs;          /* Пар агентов, синхронизированных */
} omega_multi_agent_stats_t;

/* API функции */

/**
 * omega_agent_coordinator_init - инициализация координатора
 * 
 * Return: 0 при успехе, -1 при ошибке
 */
int omega_agent_coordinator_init(void);

/**
 * omega_detect_agent_state_changes - обнаружение изменений состояния агентов
 * 
 * Отслеживает как меняется состояние каждого агента во времени.
 * 
 * @agent_id: ID агента
 * @formula_id: текущая формула/состояние
 * @timestamp: когда это произошло
 * @confidence: уверенность в этом состоянии
 * 
 * Return: количество обнаруженных новых изменений
 */
int omega_detect_agent_state_changes(uint32_t agent_id, uint64_t formula_id,
                                     int64_t timestamp, double confidence);

/**
 * omega_find_synchronized_agents - поиск синхронизированных агентов
 * 
 * Находит пары/группы агентов, которые выполняют действия одновременно
 * (в пределах временного окна max_time_delta_ms).
 * 
 * @max_time_delta_ms: максимальный временной промежуток между действиями
 * 
 * Return: количество найденных пар синхронизации
 */
int omega_find_synchronized_agents(int64_t max_time_delta_ms);

/**
 * omega_detect_coordination_patterns - обнаружение паттернов координации
 * 
 * Анализирует взаимодействия между агентами и выявляет повторяющиеся
 * паттерны (флокинг, избегание, преследование и т.д.).
 * 
 * @coordination_events: массив событий координации для анализа
 * @event_count: количество событий
 * 
 * Return: количество обнаруженных новых паттернов
 */
int omega_detect_coordination_patterns(const omega_coordination_event_t* coordination_events,
                                       int event_count);

/**
 * omega_analyze_emergent_behavior - анализ emergent поведения
 * 
 * Проверяет, демонстрирует ли группа агентов свойства, которые не 
 * являются суммой их индивидуальных поведений.
 * 
 * @agent_patterns: массив обнаруженных паттернов
 * @pattern_count: количество паттернов
 * 
 * Return: score emergent behavior (0.0-1.0)
 */
double omega_analyze_emergent_behavior(const omega_agent_pattern_t* agent_patterns,
                                       int pattern_count);

/**
 * omega_create_coordination_event - создание события координации
 * 
 * Группирует синхронизированные действия множества агентов в одно
 * координационное событие.
 * 
 * @agent_ids: массив ID агентов
 * @agent_count: количество агентов
 * @start_time: время начала
 * @coordination_strength: 0.0-1.0 насколько хорошо синхронизировано
 * @coordination_event_out: выходное событие
 * 
 * Return: 0 при успехе, -1 при ошибке
 */
int omega_create_coordination_event(const uint32_t* agent_ids, int agent_count,
                                    int64_t start_time, double coordination_strength,
                                    omega_coordination_event_t* coordination_event_out);

/**
 * omega_get_multi_agent_statistics - получить статистику мульти-агентов
 * 
 * Return: const указатель на статистику
 */
const omega_multi_agent_stats_t* omega_get_multi_agent_statistics(void);

/**
 * omega_agent_coordinator_shutdown - остановка
 */
void omega_agent_coordinator_shutdown(void);

#endif // OMEGA_AGENT_COORDINATOR_H
