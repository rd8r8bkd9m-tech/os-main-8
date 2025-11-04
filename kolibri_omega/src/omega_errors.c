/**
 * @file omega_errors.c
 * @brief Implementation of unified error handling system
 * 
 * Provides lightweight error tracking with minimal overhead, following
 * the Kolibri AI principle of energy efficiency.
 */

#include "kolibri_omega/include/omega_errors.h"
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <pthread.h>

// ==================== Internal State ====================

typedef struct {
    int initialized;
    omega_error_context_t last_error;
    omega_error_handler_t custom_handler;
    void* handler_user_data;
    pthread_mutex_t lock;
} omega_error_system_t;

static omega_error_system_t error_system = {0};

// ==================== Error String Mapping ====================

static const char* error_strings[] = {
    [OMEGA_OK] = "Success",
    [OMEGA_ERROR_GENERIC] = "Generic error",
    [OMEGA_ERROR_NOT_INITIALIZED] = "Module not initialized",
    [OMEGA_ERROR_ALREADY_INITIALIZED] = "Module already initialized",
    [OMEGA_ERROR_INVALID_STATE] = "Invalid state for operation",
    [OMEGA_ERROR_NOT_IMPLEMENTED] = "Feature not yet implemented",
    
    [OMEGA_ERROR_NO_MEMORY] = "Out of memory",
    [OMEGA_ERROR_BUFFER_FULL] = "Buffer is full",
    [OMEGA_ERROR_RESOURCE_EXHAUSTED] = "Resource limit reached",
    [OMEGA_ERROR_POOL_FULL] = "Formula pool full",
    [OMEGA_ERROR_CANVAS_FULL] = "Canvas buffer full",
    
    [OMEGA_ERROR_INVALID_FORMULA] = "Invalid formula structure",
    [OMEGA_ERROR_INVALID_RULE] = "Invalid rule structure",
    [OMEGA_ERROR_CONTRADICTION] = "Logical contradiction detected",
    [OMEGA_ERROR_INCONSISTENT_STATE] = "Inconsistent cognitive state",
    [OMEGA_ERROR_INFERENCE_FAILED] = "Inference operation failed",
    
    [OMEGA_ERROR_NULL_POINTER] = "Null pointer argument",
    [OMEGA_ERROR_INVALID_ARGUMENT] = "Invalid function argument",
    [OMEGA_ERROR_OUT_OF_RANGE] = "Value out of valid range",
    [OMEGA_ERROR_INVALID_ID] = "Invalid ID reference",
    [OMEGA_ERROR_NOT_FOUND] = "Item not found",
    
    [OMEGA_ERROR_TASK_FAILED] = "Task execution failed",
    [OMEGA_ERROR_DEADLOCK] = "Deadlock detected",
    [OMEGA_ERROR_TIMEOUT] = "Operation timeout",
    [OMEGA_ERROR_SYNC_FAILED] = "Synchronization failed"
};

// ==================== Default Error Handler ====================

static void default_error_handler(const omega_error_context_t* ctx, void* user_data) {
    (void)user_data;  // Unused
    
    fprintf(stderr, "[OMEGA ERROR] %s:%s:%d - %s (%d): %s\n",
            ctx->module ? ctx->module : "unknown",
            ctx->function ? ctx->function : "unknown",
            ctx->line,
            omega_error_string(ctx->code),
            ctx->code,
            ctx->message ? ctx->message : "no details");
}

// ==================== Public API Implementation ====================

int omega_error_system_init(void) {
    if (error_system.initialized) {
        return OMEGA_ERROR_ALREADY_INITIALIZED;
    }
    
    memset(&error_system, 0, sizeof(error_system));
    pthread_mutex_init(&error_system.lock, NULL);
    error_system.custom_handler = default_error_handler;
    error_system.initialized = 1;
    
    return OMEGA_OK;
}

void omega_error_system_shutdown(void) {
    if (!error_system.initialized) {
        return;
    }
    
    pthread_mutex_destroy(&error_system.lock);
    memset(&error_system, 0, sizeof(error_system));
}

void omega_error_set_handler(omega_error_handler_t handler, void* user_data) {
    if (!error_system.initialized) {
        return;
    }
    
    pthread_mutex_lock(&error_system.lock);
    error_system.custom_handler = handler ? handler : default_error_handler;
    error_system.handler_user_data = user_data;
    pthread_mutex_unlock(&error_system.lock);
}

void omega_error_report(omega_error_code_t code, const char* module,
                       const char* function, int line, const char* message) {
    // Even if not initialized, print to stderr
    if (!error_system.initialized) {
        fprintf(stderr, "[OMEGA ERROR] (system not initialized) %s:%s:%d - code %d: %s\n",
                module ? module : "unknown",
                function ? function : "unknown",
                line, code,
                message ? message : "no details");
        return;
    }
    
    pthread_mutex_lock(&error_system.lock);
    
    // Record error context
    error_system.last_error.code = code;
    error_system.last_error.module = module;
    error_system.last_error.function = function;
    error_system.last_error.line = line;
    error_system.last_error.message = message;
    error_system.last_error.timestamp = (uint64_t)time(NULL);
    
    // Call handler
    if (error_system.custom_handler) {
        error_system.custom_handler(&error_system.last_error, 
                                    error_system.handler_user_data);
    }
    
    pthread_mutex_unlock(&error_system.lock);
}

const char* omega_error_string(omega_error_code_t code) {
    if (code >= 0 && code < (int)(sizeof(error_strings) / sizeof(error_strings[0]))) {
        const char* str = error_strings[code];
        return str ? str : "Unknown error";
    }
    return "Invalid error code";
}

const omega_error_context_t* omega_error_get_last(void) {
    if (!error_system.initialized) {
        return NULL;
    }
    
    pthread_mutex_lock(&error_system.lock);
    const omega_error_context_t* ctx = &error_system.last_error;
    pthread_mutex_unlock(&error_system.lock);
    
    return (ctx->code != OMEGA_OK) ? ctx : NULL;
}

void omega_error_clear(void) {
    if (!error_system.initialized) {
        return;
    }
    
    pthread_mutex_lock(&error_system.lock);
    memset(&error_system.last_error, 0, sizeof(error_system.last_error));
    pthread_mutex_unlock(&error_system.lock);
}
