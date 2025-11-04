/**
 * @file omega_perf.c
 * @brief Implementation of lightweight performance profiling system
 * 
 * Provides minimal-overhead performance tracking with <1% CPU impact.
 */

#include "kolibri_omega/include/omega_perf.h"
#include "kolibri_omega/include/omega_errors.h"
#include <stdio.h>
#include <string.h>
#include <pthread.h>

// ==================== Internal State ====================

#define OMEGA_PERF_MAX_SAMPLES 1000

typedef struct {
    int initialized;
    omega_perf_stats_t stats[OMEGA_PERF_CATEGORY_COUNT];
    pthread_mutex_t lock;
    uint64_t global_start_ns;
} omega_perf_system_t;

static omega_perf_system_t perf_system = {0};

// ==================== Category Names ====================

static const char* category_names[] = {
    [OMEGA_PERF_PATTERN_DETECTION] = "Pattern Detection",
    [OMEGA_PERF_INFERENCE] = "Inference",
    [OMEGA_PERF_ABSTRACTION] = "Abstraction",
    [OMEGA_PERF_COORDINATION] = "Coordination",
    [OMEGA_PERF_PLANNING] = "Planning",
    [OMEGA_PERF_LEARNING] = "Learning",
    [OMEGA_PERF_TOTAL] = "Total"
};

// ==================== Helper Functions ====================

static inline uint64_t get_time_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        // Fallback to zero on error (shouldn't happen in practice)
        return 0;
    }
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static void update_stats(omega_perf_category_t category, uint64_t duration_ns) {
    omega_perf_stats_t* stats = &perf_system.stats[category];
    
    pthread_mutex_lock(&perf_system.lock);
    
    stats->category = category;
    stats->sample_count++;
    stats->total_ns += duration_ns;
    
    if (stats->sample_count == 1) {
        stats->min_ns = duration_ns;
        stats->max_ns = duration_ns;
    } else {
        if (duration_ns < stats->min_ns) stats->min_ns = duration_ns;
        if (duration_ns > stats->max_ns) stats->max_ns = duration_ns;
    }
    
    stats->avg_ns = stats->total_ns / stats->sample_count;
    
    // Calculate CPU usage (rough approximation)
    uint64_t elapsed = get_time_ns() - perf_system.global_start_ns;
    if (elapsed > 0) {
        stats->cpu_usage_percent = (stats->total_ns * 100.0) / elapsed;
    }
    
    pthread_mutex_unlock(&perf_system.lock);
}

// ==================== Public API Implementation ====================

int omega_perf_init(void) {
    if (perf_system.initialized) {
        return OMEGA_ERROR_ALREADY_INITIALIZED;
    }
    
    memset(&perf_system, 0, sizeof(perf_system));
    pthread_mutex_init(&perf_system.lock, NULL);
    perf_system.global_start_ns = get_time_ns();
    perf_system.initialized = 1;
    
    // Initialize min values to max
    for (int i = 0; i < OMEGA_PERF_CATEGORY_COUNT; i++) {
        perf_system.stats[i].min_ns = UINT64_MAX;
    }
    
    return OMEGA_OK;
}

void omega_perf_shutdown(void) {
    if (!perf_system.initialized) {
        return;
    }
    
    pthread_mutex_destroy(&perf_system.lock);
    memset(&perf_system, 0, sizeof(perf_system));
}

omega_perf_handle_t omega_perf_start(omega_perf_category_t category) {
    omega_perf_handle_t handle;
    handle.start_ns = get_time_ns();
    handle.category = category;
    return handle;
}

uint64_t omega_perf_end(omega_perf_handle_t handle) {
    uint64_t end_ns = get_time_ns();
    uint64_t duration_ns = end_ns - handle.start_ns;
    
    if (perf_system.initialized) {
        update_stats(handle.category, duration_ns);
    }
    
    return duration_ns;
}

const omega_perf_stats_t* omega_perf_get_stats(omega_perf_category_t category) {
    if (!perf_system.initialized || category >= OMEGA_PERF_CATEGORY_COUNT) {
        return NULL;
    }
    
    pthread_mutex_lock(&perf_system.lock);
    const omega_perf_stats_t* stats = &perf_system.stats[category];
    pthread_mutex_unlock(&perf_system.lock);
    
    return (stats->sample_count > 0) ? stats : NULL;
}

void omega_perf_reset(void) {
    if (!perf_system.initialized) {
        return;
    }
    
    pthread_mutex_lock(&perf_system.lock);
    memset(&perf_system.stats, 0, sizeof(perf_system.stats));
    perf_system.global_start_ns = get_time_ns();
    
    // Reinitialize min values
    for (int i = 0; i < OMEGA_PERF_CATEGORY_COUNT; i++) {
        perf_system.stats[i].min_ns = UINT64_MAX;
    }
    pthread_mutex_unlock(&perf_system.lock);
}

void omega_perf_print_report(void) {
    if (!perf_system.initialized) {
        printf("[Performance] System not initialized\n");
        return;
    }
    
    printf("\n╔════════════════════════════════════════════════════════════════╗\n");
    printf("║              Kolibri-Omega Performance Report                 ║\n");
    printf("╠════════════════════════════════════════════════════════════════╣\n");
    printf("║ Category            │ Samples │   Avg    │   Min    │   Max   ║\n");
    printf("╠════════════════════════════════════════════════════════════════╣\n");
    
    pthread_mutex_lock(&perf_system.lock);
    
    for (int i = 0; i < OMEGA_PERF_CATEGORY_COUNT; i++) {
        const omega_perf_stats_t* stats = &perf_system.stats[i];
        if (stats->sample_count > 0) {
            printf("║ %-19s │ %7lu │ %6lu µs │ %6lu µs │ %6lu µs ║\n",
                   category_names[i],
                   (unsigned long)stats->sample_count,
                   (unsigned long)(stats->avg_ns / 1000),
                   (unsigned long)(stats->min_ns / 1000),
                   (unsigned long)(stats->max_ns / 1000));
        }
    }
    
    pthread_mutex_unlock(&perf_system.lock);
    
    printf("╚════════════════════════════════════════════════════════════════╝\n");
}

const char* omega_perf_category_name(omega_perf_category_t category) {
    if (category >= 0 && category < OMEGA_PERF_CATEGORY_COUNT) {
        return category_names[category];
    }
    return "Unknown";
}
