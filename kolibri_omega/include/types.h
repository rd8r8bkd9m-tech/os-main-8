#ifndef KOLIBRI_OMEGA_TYPES_H
#define KOLIBRI_OMEGA_TYPES_H

#include <pthread.h>
#include <stdint.h>
#include <stddef.h>
#include "forward.h"

// --- KF Pool Types ---
#define MAX_FORMULAS 1024
#define MAX_PREDICATES 4

typedef enum {
    KF_TYPE_FACT,
    KF_TYPE_RULE
} kf_formula_type;

struct kf_predicate_s {
    char name[50];
    char value[50];
};

struct kf_formula_s {
    uint64_t id;
    kf_formula_type type;
    int is_valid;
    int time;
    union {
        struct {
            int object_id;
            kf_predicate_t predicates[MAX_PREDICATES];
            size_t num_predicates;
        } fact;
        struct {
            uint64_t condition_formula_id;
            uint64_t consequence_formula_id;
            double confidence;
        } rule;
    } data;
};

struct kf_pool_s {
    kf_formula_t formulas[MAX_FORMULAS];
    size_t count;
    uint64_t next_id;
};

// --- Sigma Coordinator Types ---
#define MAX_TASKS 100

typedef enum {
    TASK_CONTRADICTION,
    TASK_INVALID_RULE
} sigma_task_type;

typedef enum {
    TASK_STATUS_OPEN,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_DONE,
    TASK_STATUS_FAILED
} sigma_task_status_t;

struct sigma_task_s {
    uint64_t id;
    sigma_task_type type;
    sigma_task_status_t status; // Статус задачи
    union {
        struct { uint64_t formula_ids[2]; } contradiction;
        struct { uint64_t rule_id; } invalid_rule;
    } data;
};

struct sigma_coordinator_s {
    sigma_task_t tasks[MAX_TASKS];
    int count;
    uint64_t next_task_id;
    size_t next_task_to_process; // Индекс для следующей задачи для обработки
};

// --- Canvas Types ---
#define MAX_CANVAS_ITEMS 256

typedef enum {
    OMEGA_HYPOTHESIS_FACT,
    OMEGA_HYPOTHESIS_PREDICTION,
    OMEGA_HYPOTHESIS_DREAM
} omega_hypothesis_type;

struct omega_canvas_item_s {
    uint64_t id; // Уникальный ID элемента на холсте
    omega_hypothesis_type type;
    uint64_t formula_id;
    uint64_t derived_from_rule_id; // 0 если это просто факт
    int timestamp; // Время добавления на холст
};

struct omega_canvas_s {
    omega_canvas_item_t items[MAX_CANVAS_ITEMS];
    size_t count;
    uint64_t next_item_id; // ID для следующего элемента
    kf_pool_t* formula_pool;
};

// --- Cognitive Module Types ---
#define OBSERVER_SLEEP_US 10000

struct omega_observer_s {
    omega_canvas_t* canvas;
    sigma_coordinator_t* coordinator;
};

struct omega_dreamer_s {
    omega_canvas_t* canvas;
    kf_pool_t* formula_pool;
    sigma_coordinator_t* coordinator;
    int next_object_id;
};

struct omega_solver_lobe_s {
    sigma_coordinator_t* coordinator;
    kf_pool_t* formula_pool;
};

struct omega_predictor_lobe_s {
    omega_canvas_t* canvas;
    kf_pool_t* formula_pool;
};

// --- Sandbox Types ---
#define MAX_OBJECTS 10

struct sandbox_object_s {
    int id;
    float y;      // Позиция по Y
    float vy;     // Скорость по Y
};

struct sandbox_world_s {
    sandbox_object_t objects[MAX_OBJECTS];
    size_t num_objects;
    float gravity;
};

#endif // KOLIBRI_OMEGA_TYPES_H
