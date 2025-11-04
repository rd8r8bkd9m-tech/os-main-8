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

const char* omega_error_string(omega_error_code_t code) {
    switch (code) {
        case OMEGA_OK: return "Success";
        
        // General errors (1-99)
        case OMEGA_ERROR_GENERIC: return "Generic error";
        case OMEGA_ERROR_NOT_INITIALIZED: return "Module not initialized";
        case OMEGA_ERROR_ALREADY_INITIALIZED: return "Module already initialized";
        case OMEGA_ERROR_INVALID_STATE: return "Invalid state for operation";
        case OMEGA_ERROR_NOT_IMPLEMENTED: return "Feature not yet implemented";
        
        // Memory/resource errors (100-199)
        case OMEGA_ERROR_NO_MEMORY: return "Out of memory";
        case OMEGA_ERROR_BUFFER_FULL: return "Buffer is full";
        case OMEGA_ERROR_RESOURCE_EXHAUSTED: return "Resource limit reached";
        case OMEGA_ERROR_POOL_FULL: return "Formula pool full";
        case OMEGA_ERROR_CANVAS_FULL: return "Canvas buffer full";
        
        // Logic/reasoning errors (200-299)
        case OMEGA_ERROR_INVALID_FORMULA: return "Invalid formula structure";
        case OMEGA_ERROR_INVALID_RULE: return "Invalid rule structure";
        case OMEGA_ERROR_CONTRADICTION: return "Logical contradiction detected";
        case OMEGA_ERROR_INCONSISTENT_STATE: return "Inconsistent cognitive state";
        case OMEGA_ERROR_INFERENCE_FAILED: return "Inference operation failed";
        
        // Data validation errors (300-399)
        case OMEGA_ERROR_NULL_POINTER: return "Null pointer argument";
        case OMEGA_ERROR_INVALID_ARGUMENT: return "Invalid function argument";
        case OMEGA_ERROR_OUT_OF_RANGE: return "Value out of valid range";
        case OMEGA_ERROR_INVALID_ID: return "Invalid ID reference";
        case OMEGA_ERROR_NOT_FOUND: return "Item not found";
        
        // Coordination errors (400-499)
        case OMEGA_ERROR_TASK_FAILED: return "Task execution failed";
        case OMEGA_ERROR_DEADLOCK: return "Deadlock detected";
        case OMEGA_ERROR_TIMEOUT: return "Operation timeout";
        case OMEGA_ERROR_SYNC_FAILED: return "Synchronization failed";
        
        default: return "Unknown error code";
    }
}

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

// omega_error_string is now defined above, before it's used

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
