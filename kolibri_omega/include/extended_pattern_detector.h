#ifndef OMEGA_EXTENDED_PATTERN_DETECTOR_H
#define OMEGA_EXTENDED_PATTERN_DETECTOR_H

#include <stdint.h>
#include <stddef.h>

/**
 * Extended Pattern Detector Header - Phase 3 Component
 * 
 * Детектор паттернов для последовательностей из 3-10 шагов.
 */

#define OMEGA_MAX_PATTERN_LENGTH 10

/**
 * omega_pattern_step_t - отдельный шаг в паттерне
 */
typedef struct {
    uint64_t formula_id;
    int64_t timestamp;
    double confidence;
} omega_pattern_step_t;

/**
 * omega_extended_pattern_t - полный паттерн из 3+ шагов
 */
typedef struct {
    uint64_t pattern_id;
    omega_pattern_step_t steps[OMEGA_MAX_PATTERN_LENGTH];
    int step_count;
    double overall_confidence;
    int64_t timing_variance;
} omega_extended_pattern_t;

/**
 * omega_pattern_statistics_t - статистика по паттернам
 */
typedef struct {
    int total_patterns;
    int patterns_by_length[OMEGA_MAX_PATTERN_LENGTH + 1];
    double average_confidence;
    int min_length;
    int max_length;
} omega_pattern_statistics_t;

/* API функции */

int omega_extended_pattern_detector_init(void);

int omega_validate_temporal_constraint(int64_t timestamp1, int64_t timestamp2,
                                        int64_t max_time_delta_ms);

double omega_compute_transition_probabilities(const omega_extended_pattern_t* pattern,
                                              int step_index);

int omega_predict_next_pattern_step(const omega_extended_pattern_t* pattern,
                                    omega_pattern_step_t* next_step_out);

int omega_detect_extended_patterns(const void* facts, int fact_count, int64_t current_time);

const omega_pattern_statistics_t* omega_get_pattern_statistics(void);

void omega_extended_pattern_detector_shutdown(void);

#endif // OMEGA_EXTENDED_PATTERN_DETECTOR_H
