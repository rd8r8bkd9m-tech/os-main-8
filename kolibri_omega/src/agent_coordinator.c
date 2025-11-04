#include "kolibri_omega/include/agent_coordinator.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define OMEGA_MAX_AGENT_STATES 200

typedef struct {
    omega_agent_state_t agent_states[OMEGA_MAX_AGENT_STATES];
    int state_count;
    
    omega_agent_pattern_t patterns[OMEGA_MAX_AGENT_PATTERNS];
    int pattern_count;
    
    int unique_agents;
    omega_multi_agent_stats_t stats;
} omega_agent_coordinator_ctx_t;

static omega_agent_coordinator_ctx_t coordinator_ctx = {0};

/**
 * omega_agent_coordinator_init - инициализация
 */
int omega_agent_coordinator_init(void) {
    memset(&coordinator_ctx, 0, sizeof(coordinator_ctx));
    
    printf("[AgentCoordinator] Initialized for tracking up to %d agents\n",
           OMEGA_MAX_AGENTS);
    
    return 0;
}

/**
 * omega_detect_agent_state_changes - обнаружение изменений
 */
int omega_detect_agent_state_changes(uint32_t agent_id, uint64_t formula_id,
                                     int64_t timestamp, double confidence) {
    if (coordinator_ctx.state_count >= OMEGA_MAX_AGENT_STATES) {
        return 0;  // Переполнение
    }
    
    // Проверяем, есть ли уже состояния этого агента
    int found_agent = 0;
    for (int i = 0; i < coordinator_ctx.state_count; i++) {
        if (coordinator_ctx.agent_states[i].agent_id == agent_id) {
            found_agent = 1;
            break;
        }
    }
    
    // Сохраняем новое состояние
    coordinator_ctx.agent_states[coordinator_ctx.state_count].agent_id = agent_id;
    coordinator_ctx.agent_states[coordinator_ctx.state_count].formula_id = formula_id;
    coordinator_ctx.agent_states[coordinator_ctx.state_count].timestamp = timestamp;
    coordinator_ctx.agent_states[coordinator_ctx.state_count].confidence = confidence;
    
    coordinator_ctx.state_count++;
    
    if (!found_agent) {
        coordinator_ctx.unique_agents++;
    }
    
    printf("[AgentCoordinator] Agent %u changed state to formula %lu at time %ld "
           "(confidence: %.2f)\n", agent_id, (unsigned long)formula_id, (long)timestamp, confidence);
    
    return 1;  // Одно изменение обнаружено
}

/**
 * omega_find_synchronized_agents - поиск синхронизированных агентов
 */
int omega_find_synchronized_agents(int64_t max_time_delta_ms) {
    int synchronized_pairs = 0;
    
    // Проверяем все пары агентов
    for (int i = 0; i < coordinator_ctx.state_count - 1; i++) {
        for (int j = i + 1; j < coordinator_ctx.state_count; j++) {
            omega_agent_state_t* state_i = &coordinator_ctx.agent_states[i];
            omega_agent_state_t* state_j = &coordinator_ctx.agent_states[j];
            
            // Если агенты разные но действия произошли близко во времени
            if (state_i->agent_id != state_j->agent_id) {
                int64_t time_delta = state_j->timestamp - state_i->timestamp;
                if (time_delta >= 0 && time_delta <= max_time_delta_ms) {
                    printf("[AgentCoordinator] Synchronized pair: Agent %u ↔ Agent %u "
                           "(time delta: %ld ms)\n",
                           state_i->agent_id, state_j->agent_id, (long)time_delta);
                    synchronized_pairs++;
                    coordinator_ctx.stats.synchronization_pairs++;
                }
            }
        }
    }
    
    return synchronized_pairs;
}

/**
 * omega_detect_coordination_patterns - обнаружение паттернов
 */
int omega_detect_coordination_patterns(const omega_coordination_event_t* coordination_events,
                                       int event_count) {
    if (!coordination_events || event_count == 0) {
        return 0;
    }
    
    int new_patterns = 0;
    
    // Анализируем события координации
    for (int i = 0; i < event_count && coordinator_ctx.pattern_count < OMEGA_MAX_AGENT_PATTERNS; i++) {
        const omega_coordination_event_t* event = &coordination_events[i];
        
        // Создаем паттерн из события координации
        omega_agent_pattern_t* pattern = &coordinator_ctx.patterns[coordinator_ctx.pattern_count];
        
        pattern->pattern_id = 3000 + coordinator_ctx.pattern_count;
        pattern->agent_count = event->agent_count;
        
        for (int j = 0; j < event->agent_count; j++) {
            pattern->agent_ids[j] = event->agent_ids[j];
        }
        
        pattern->average_confidence = event->pattern_confidence;
        pattern->occurrences = 1;
        
        // Определяем тип паттерна по coordination_strength
        if (event->coordination_strength > 0.8) {
            pattern->pattern_type = 0;  // Флокинг (высокая синхронность)
        } else if (event->coordination_strength > 0.5) {
            pattern->pattern_type = 1;  // Избегание (средняя синхронность)
        } else {
            pattern->pattern_type = 3;  // Другое
        }
        
        printf("[AgentCoordinator] Detected coordination pattern %lu: %d agents "
               "(type: %d, strength: %.2f)\n",
               (unsigned long)pattern->pattern_id, pattern->agent_count, pattern->pattern_type,
               event->coordination_strength);
        
        coordinator_ctx.pattern_count++;
        coordinator_ctx.stats.total_patterns++;
        new_patterns++;
    }
    
    return new_patterns;
}

/**
 * omega_analyze_emergent_behavior - анализ emergent поведения
 */
double omega_analyze_emergent_behavior(const omega_agent_pattern_t* agent_patterns,
                                       int pattern_count) {
    if (!agent_patterns || pattern_count == 0) {
        return 0.0;
    }
    
    // Простой метод: если несколько агентов взаимодействуют координированно,
    // это emergent behavior
    
    double emergent_score = 0.0;
    int multi_agent_patterns = 0;
    
    for (int i = 0; i < pattern_count; i++) {
        if (agent_patterns[i].agent_count > 1) {
            // Мульти-агентный паттерн
            multi_agent_patterns++;
            emergent_score += agent_patterns[i].average_confidence / pattern_count;
        }
    }
    
    if (multi_agent_patterns > 0) {
        emergent_score = (double)multi_agent_patterns / pattern_count;
        printf("[AgentCoordinator] Emergent behavior detected: score %.3f "
               "(%d multi-agent patterns)\n", emergent_score, multi_agent_patterns);
    }
    
    return emergent_score;
}

/**
 * omega_create_coordination_event - создание события
 */
int omega_create_coordination_event(const uint32_t* agent_ids, int agent_count,
                                    int64_t start_time, double coordination_strength,
                                    omega_coordination_event_t* coordination_event_out) {
    if (!agent_ids || !coordination_event_out || agent_count == 0 || agent_count > OMEGA_MAX_AGENTS) {
        return -1;
    }
    
    coordination_event_out->coordination_id = 4000 + coordinator_ctx.stats.total_coordination_events;
    coordination_event_out->agent_count = agent_count;
    
    for (int i = 0; i < agent_count; i++) {
        coordination_event_out->agent_ids[i] = agent_ids[i];
    }
    
    coordination_event_out->start_timestamp = start_time;
    coordination_event_out->end_timestamp = start_time + 50;  // Типичная длительность
    
    coordination_event_out->coordination_strength = coordination_strength;
    coordination_event_out->coordination_type = (coordination_strength > 0.7) ? 0 : 1;
    coordination_event_out->pattern_confidence = 0.8 * 1.0;  // Базовая уверенность
    
    coordinator_ctx.stats.total_coordination_events++;
    coordinator_ctx.stats.average_coordination_strength += coordination_strength;
    
    printf("[AgentCoordinator] Created coordination event %lu: %d agents, "
           "strength %.2f\n",
           (unsigned long)coordination_event_out->coordination_id, agent_count, coordination_strength);
    
    return 0;
}

/**
 * omega_get_multi_agent_statistics - получить статистику
 */
const omega_multi_agent_stats_t* omega_get_multi_agent_statistics(void) {
    coordinator_ctx.stats.total_agents = coordinator_ctx.unique_agents;
    coordinator_ctx.stats.total_coordination_events = 0;  // Count events properly
    coordinator_ctx.stats.total_patterns = coordinator_ctx.pattern_count;
    
    if (coordinator_ctx.pattern_count > 0) {
        int flocking_count = 0;
        for (int i = 0; i < coordinator_ctx.pattern_count; i++) {
            if (coordinator_ctx.patterns[i].pattern_type == 0) {
                flocking_count++;
            }
        }
        coordinator_ctx.stats.most_common_pattern_type = (flocking_count > 0) ? 0 : 3;
    }
    
    return &coordinator_ctx.stats;
}

/**
 * omega_agent_coordinator_shutdown - остановка
 */
void omega_agent_coordinator_shutdown(void) {
    printf("[AgentCoordinator] Shutdown: tracked %d agents, detected %d patterns, "
           "%d coordination events\n",
           coordinator_ctx.unique_agents, coordinator_ctx.pattern_count,
           coordinator_ctx.stats.total_coordination_events);
    memset(&coordinator_ctx, 0, sizeof(coordinator_ctx));
}
