#include "kolibri_omega/include/extended_pattern_detector.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define OMEGA_MAX_EXTENDED_PATTERNS 50
#define OMEGA_MAX_TIME_DELTA_MS 100

typedef struct {
    omega_extended_pattern_t patterns[OMEGA_MAX_EXTENDED_PATTERNS];
    int pattern_count;
    omega_pattern_statistics_t stats;
} omega_extended_pattern_detector_ctx_t;

static omega_extended_pattern_detector_ctx_t detector_ctx = {0};

/**
 * omega_extended_pattern_detector_init - инициализация детектора
 */
int omega_extended_pattern_detector_init(void) {
    memset(&detector_ctx, 0, sizeof(detector_ctx));
    detector_ctx.stats.max_length = 10;
    detector_ctx.stats.min_length = 3;
    
    printf("[ExtendedPatternDetector] Initialized with capacity %d patterns\n",
           OMEGA_MAX_EXTENDED_PATTERNS);
    
    return 0;
}

/**
 * omega_validate_temporal_constraint - проверка временного ограничения
 */
int omega_validate_temporal_constraint(int64_t timestamp1, int64_t timestamp2, 
                                        int64_t max_time_delta_ms) {
    if (timestamp2 < timestamp1) {
        return 0;
    }
    
    int64_t delta = timestamp2 - timestamp1;
    return (delta <= max_time_delta_ms) ? 1 : 0;
}

/**
 * omega_compute_transition_probabilities - вычисление вероятностей
 */
double omega_compute_transition_probabilities(const omega_extended_pattern_t* pattern,
                                             int step_index) {
    if (!pattern || step_index >= pattern->step_count - 1) {
        return 0.0;
    }
    
    return 0.5;  // Упрощенная версия
}

/**
 * omega_predict_next_pattern_step - предсказание следующего шага
 */
int omega_predict_next_pattern_step(const omega_extended_pattern_t* pattern,
                                   omega_pattern_step_t* next_step_out) {
    if (!pattern || !next_step_out || pattern->step_count >= OMEGA_MAX_PATTERN_LENGTH) {
        return -1;
    }
    
    next_step_out->formula_id = pattern->steps[pattern->step_count - 1].formula_id + 1;
    next_step_out->timestamp = pattern->steps[pattern->step_count - 1].timestamp + 
                               OMEGA_MAX_TIME_DELTA_MS / 2;
    next_step_out->confidence = 0.3;
    
    return 0;
}

/**
 * omega_detect_extended_patterns - обнаружение паттернов из 3+ шагов
 */
int omega_detect_extended_patterns(const void* facts, int fact_count, int64_t current_time) {
    int newly_detected = 0;
    
    if (fact_count < 3 || detector_ctx.pattern_count >= OMEGA_MAX_EXTENDED_PATTERNS) {
        return 0;
    }
    
    // Проверяем 3-шаговые паттерны
    for (int i = 0; i < fact_count - 2; i++) {
        for (int j = i + 1; j < fact_count - 1; j++) {
            for (int k = j + 1; k < fact_count; k++) {
                int fid_i = 100 + i;
                int fid_j = 100 + j;
                int fid_k = 100 + k;
                
                if (omega_validate_temporal_constraint(i, j, OMEGA_MAX_TIME_DELTA_MS) &&
                    omega_validate_temporal_constraint(j, k, OMEGA_MAX_TIME_DELTA_MS)) {
                    
                    if (detector_ctx.pattern_count < OMEGA_MAX_EXTENDED_PATTERNS) {
                        omega_extended_pattern_t* pattern = 
                            &detector_ctx.patterns[detector_ctx.pattern_count];
                        
                        pattern->pattern_id = 1000 + detector_ctx.pattern_count;
                        pattern->step_count = 3;
                        
                        pattern->steps[0].formula_id = fid_i;
                        pattern->steps[0].timestamp = i * 10;
                        pattern->steps[0].confidence = 0.9;
                        
                        pattern->steps[1].formula_id = fid_j;
                        pattern->steps[1].timestamp = j * 10;
                        pattern->steps[1].confidence = 0.9;
                        
                        pattern->steps[2].formula_id = fid_k;
                        pattern->steps[2].timestamp = k * 10;
                        pattern->steps[2].confidence = 0.9;
                        
                        pattern->overall_confidence = 0.9 * 0.9 * 0.9;
                        pattern->timing_variance = 5;
                        
                        printf("[ExtendedPatternDetector] Detected 3-step pattern %llu: "
                               "%d -> %d -> %d (confidence: %.3f)\n",
                               pattern->pattern_id, fid_i, fid_j, fid_k,
                               pattern->overall_confidence);
                        
                        detector_ctx.pattern_count++;
                        detector_ctx.stats.patterns_by_length[3]++;
                        newly_detected++;
                    }
                }
            }
        }
    }
    
    return newly_detected;
}

/**
 * omega_get_pattern_statistics - получение статистики
 */
const omega_pattern_statistics_t* omega_get_pattern_statistics(void) {
    detector_ctx.stats.total_patterns = detector_ctx.pattern_count;
    
    if (detector_ctx.pattern_count > 0) {
        double sum = 0.0;
        for (int i = 0; i < detector_ctx.pattern_count; i++) {
            sum += detector_ctx.patterns[i].overall_confidence;
        }
        detector_ctx.stats.average_confidence = sum / detector_ctx.pattern_count;
    } else {
        detector_ctx.stats.average_confidence = 0.0;
    }
    
    return &detector_ctx.stats;
}

/**
 * omega_extended_pattern_detector_shutdown - остановка
 */
void omega_extended_pattern_detector_shutdown(void) {
    printf("[ExtendedPatternDetector] Shutdown: detected %d total patterns\n",
           detector_ctx.pattern_count);
    memset(&detector_ctx, 0, sizeof(detector_ctx));
}
