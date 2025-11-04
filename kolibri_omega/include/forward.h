#ifndef KOLIBRI_OMEGA_FORWARD_H
#define KOLIBRI_OMEGA_FORWARD_H

// Предварительные объявления всех основных структур
// Это позволяет заголовочным файлам ссылаться на типы по указателю,
// не зная их полного определения, что разрывает циклы зависимостей.

typedef struct kf_predicate_s kf_predicate_t;
typedef struct kf_formula_s kf_formula_t;
typedef struct kf_pool_s kf_pool_t;

typedef struct sigma_task_s sigma_task_t;
typedef struct sigma_coordinator_s sigma_coordinator_t;

typedef struct omega_canvas_item_s omega_canvas_item_t;
typedef struct omega_canvas_s omega_canvas_t;

typedef struct omega_observer_s omega_observer_t;
typedef struct omega_dreamer_s omega_dreamer_t;
typedef struct omega_solver_lobe_s omega_solver_lobe_t;
typedef struct omega_predictor_lobe_s omega_predictor_lobe_t;

typedef struct sandbox_object_s sandbox_object_t;
typedef struct sandbox_world_s sandbox_world_t;

#endif // KOLIBRI_OMEGA_FORWARD_H
