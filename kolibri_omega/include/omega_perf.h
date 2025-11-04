#ifndef KOLIBRI_OMEGA_PERF_H
#define KOLIBRI_OMEGA_PERF_H

/**
 * @file omega_perf.h
 * @brief Lightweight performance profiling system for Kolibri-Omega
 * 
 * Provides minimal-overhead performance measurement tools for profiling
 * cognitive operations. Designed for energy efficiency and real-time monitoring.
 * 
 * @author Kolibri AI Team
 * @date November 4, 2025
 */

#include <stdint.h>
#include <time.h>

// ==================== Performance Counter Types ====================

/**
 * @brief Performance counter categories
 */
typedef enum {
    OMEGA_PERF_PATTERN_DETECTION = 0,
    OMEGA_PERF_INFERENCE,
    OMEGA_PERF_ABSTRACTION,
    OMEGA_PERF_COORDINATION,
    OMEGA_PERF_PLANNING,
    OMEGA_PERF_LEARNING,
    OMEGA_PERF_TOTAL,
    OMEGA_PERF_CATEGORY_COUNT
} omega_perf_category_t;

/**
 * @brief Performance measurement sample
 */
typedef struct {
    uint64_t start_ns;              // Start time in nanoseconds
    uint64_t end_ns;                // End time in nanoseconds
    uint64_t duration_ns;           // Duration in nanoseconds
    omega_perf_category_t category; // Category of measurement
} omega_perf_sample_t;

/**
 * @brief Aggregated performance statistics
 */
typedef struct {
    omega_perf_category_t category;
    uint64_t sample_count;          // Number of samples
    uint64_t total_ns;              // Total time spent
    uint64_t min_ns;                // Minimum duration
    uint64_t max_ns;                // Maximum duration
    uint64_t avg_ns;                // Average duration
    double cpu_usage_percent;       // CPU usage percentage
} omega_perf_stats_t;

/**
 * @brief Performance profiler handle
 */
typedef struct {
    uint64_t start_ns;
    omega_perf_category_t category;
} omega_perf_handle_t;

// ==================== Public API ====================

/**
 * @brief Initialize performance profiling system
 * @return 0 on success, error code on failure
 */
int omega_perf_init(void);

/**
 * @brief Shutdown performance profiling system
 */
void omega_perf_shutdown(void);

/**
 * @brief Start performance measurement
 * @param category Performance category
 * @return Performance handle
 */
omega_perf_handle_t omega_perf_start(omega_perf_category_t category);

/**
 * @brief End performance measurement
 * @param handle Performance handle from omega_perf_start
 * @return Duration in nanoseconds
 */
uint64_t omega_perf_end(omega_perf_handle_t handle);

/**
 * @brief Get performance statistics for a category
 * @param category Performance category
 * @return Pointer to statistics (NULL if not available)
 */
const omega_perf_stats_t* omega_perf_get_stats(omega_perf_category_t category);

/**
 * @brief Reset all performance statistics
 */
void omega_perf_reset(void);

/**
 * @brief Print performance report to stdout
 */
void omega_perf_print_report(void);

/**
 * @brief Get category name as string
 * @param category Performance category
 * @return Category name
 */
const char* omega_perf_category_name(omega_perf_category_t category);

// ==================== Convenience Macros ====================

/**
 * @brief Measure performance of a code block
 * Usage:
 *   OMEGA_PERF_MEASURE(OMEGA_PERF_PATTERN_DETECTION) {
 *       // Code to measure
 *   }
 */
#define OMEGA_PERF_MEASURE(cat) \
    for (omega_perf_handle_t _perf_h = omega_perf_start(cat), _done = {0}; \
         !_done.start_ns; \
         omega_perf_end(_perf_h), _done.start_ns = 1)

/**
 * @brief Simple inline performance measurement
 */
#define OMEGA_PERF_START(cat) omega_perf_handle_t _perf_##cat = omega_perf_start(cat)
#define OMEGA_PERF_END(cat) omega_perf_end(_perf_##cat)

#endif // KOLIBRI_OMEGA_PERF_H
