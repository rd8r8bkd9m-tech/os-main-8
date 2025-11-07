#ifndef KOLIBRI_OMEGA_ERRORS_H
#define KOLIBRI_OMEGA_ERRORS_H

/**
 * @file omega_errors.h
 * @brief Unified error handling system for Kolibri-Omega cognitive architecture
 * 
 * This module provides standardized error codes, error reporting, and recovery
 * mechanisms across all cognitive components. Following the Kolibri AI philosophy
 * of lightweight, precise, and energy-efficient solutions.
 * 
 * @author Kolibri AI Team
 * @date November 4, 2025
 */

#include <stdint.h>

/**
 * @brief Omega error codes - standardized across all modules
 * 
 * Range allocation:
 * - 0: Success
 * - 1-99: General errors
 * - 100-199: Memory/resource errors
 * - 200-299: Logic/reasoning errors
 * - 300-399: Data validation errors
 * - 400-499: Coordination errors
 */
typedef enum {
    OMEGA_OK = 0,                      // Success
    
    // General errors (1-99)
    OMEGA_ERROR_GENERIC = 1,           // Generic unspecified error
    OMEGA_ERROR_NOT_INITIALIZED = 2,   // Module not initialized
    OMEGA_ERROR_ALREADY_INITIALIZED = 3, // Module already initialized
    OMEGA_ERROR_INVALID_STATE = 4,     // Invalid state for operation
    OMEGA_ERROR_NOT_IMPLEMENTED = 5,   // Feature not yet implemented
    
    // Memory/resource errors (100-199)
    OMEGA_ERROR_NO_MEMORY = 100,       // Out of memory
    OMEGA_ERROR_BUFFER_FULL = 101,     // Buffer is full
    OMEGA_ERROR_RESOURCE_EXHAUSTED = 102, // Resource limit reached
    OMEGA_ERROR_POOL_FULL = 103,       // Formula pool full
    OMEGA_ERROR_CANVAS_FULL = 104,     // Canvas buffer full
    
    // Logic/reasoning errors (200-299)
    OMEGA_ERROR_INVALID_FORMULA = 200, // Invalid formula structure
    OMEGA_ERROR_INVALID_RULE = 201,    // Invalid rule structure
    OMEGA_ERROR_CONTRADICTION = 202,   // Logical contradiction detected
    OMEGA_ERROR_INCONSISTENT_STATE = 203, // Inconsistent cognitive state
    OMEGA_ERROR_INFERENCE_FAILED = 204,   // Inference operation failed
    
    // Data validation errors (300-399)
    OMEGA_ERROR_NULL_POINTER = 300,    // Null pointer argument
    OMEGA_ERROR_INVALID_ARGUMENT = 301, // Invalid function argument
    OMEGA_ERROR_OUT_OF_RANGE = 302,    // Value out of valid range
    OMEGA_ERROR_INVALID_ID = 303,      // Invalid ID reference
    OMEGA_ERROR_NOT_FOUND = 304,       // Item not found
    
    // Coordination errors (400-499)
    OMEGA_ERROR_TASK_FAILED = 400,     // Task execution failed
    OMEGA_ERROR_DEADLOCK = 401,        // Deadlock detected
    OMEGA_ERROR_TIMEOUT = 402,         // Operation timeout
    OMEGA_ERROR_SYNC_FAILED = 403      // Synchronization failed
} omega_error_code_t;

/**
 * @brief Error context - detailed information about an error
 */
typedef struct {
    omega_error_code_t code;           // Error code
    const char* module;                // Module where error occurred
    const char* function;              // Function where error occurred
    int line;                          // Line number where error occurred
    const char* message;               // Human-readable error message
    uint64_t timestamp;                // Timestamp of error
} omega_error_context_t;

/**
 * @brief Error handler callback type
 * @param ctx Error context information
 * @param user_data User-provided data
 */
typedef void (*omega_error_handler_t)(const omega_error_context_t* ctx, void* user_data);

// ==================== Public API ====================

/**
 * @brief Initialize the error handling system
 * @return OMEGA_OK on success
 */
int omega_error_system_init(void);

/**
 * @brief Shutdown the error handling system
 */
void omega_error_system_shutdown(void);

/**
 * @brief Set a custom error handler
 * @param handler Error handler callback
 * @param user_data User data passed to callback
 */
void omega_error_set_handler(omega_error_handler_t handler, void* user_data);

/**
 * @brief Report an error
 * @param code Error code
 * @param module Module name
 * @param function Function name
 * @param line Line number
 * @param message Error message
 */
void omega_error_report(omega_error_code_t code, const char* module,
                       const char* function, int line, const char* message);

/**
 * @brief Get human-readable error string
 * @param code Error code
 * @return Error description string
 */
const char* omega_error_string(omega_error_code_t code);

/**
 * @brief Get the last error that occurred
 * @return Pointer to last error context (NULL if no error)
 */
const omega_error_context_t* omega_error_get_last(void);

/**
 * @brief Clear the last error
 */
void omega_error_clear(void);

// ==================== Convenience Macros ====================

/**
 * @brief Report error with automatic module/function/line info
 */
#define OMEGA_ERROR(code, msg) \
    omega_error_report(code, __FILE__, __func__, __LINE__, msg)

/**
 * @brief Check condition and report error if false
 */
#define OMEGA_CHECK(cond, code, msg) \
    do { \
        if (!(cond)) { \
            OMEGA_ERROR(code, msg); \
            return code; \
        } \
    } while (0)

/**
 * @brief Check pointer not null
 */
#define OMEGA_CHECK_NOT_NULL(ptr) \
    OMEGA_CHECK(ptr != NULL, OMEGA_ERROR_NULL_POINTER, #ptr " is NULL")

/**
 * @brief Return on error
 */
#define OMEGA_RETURN_ON_ERROR(call) \
    do { \
        int _err = (call); \
        if (_err != OMEGA_OK) { \
            return _err; \
        } \
    } while (0)

#endif // KOLIBRI_OMEGA_ERRORS_H
