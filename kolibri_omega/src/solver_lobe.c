#include "kolibri_omega/include/types.h"
#include "kolibri_omega/include/solver_lobe.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include "kolibri_omega/stubs/sigma_coordinator_stub.h"
#include <stdio.h>

#include "kolibri_omega/include/types.h"
#include "kolibri_omega/include/solver_lobe.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include "kolibri_omega/stubs/sigma_coordinator_stub.h"
#include <stdio.h>

/**
 * @brief Инициализирует Лоб-Решатель.
 */
void omega_solver_lobe_init(omega_solver_lobe_t* lobe, sigma_coordinator_t* coordinator, kf_pool_t* formula_pool) {
    lobe->coordinator = coordinator;
    lobe->formula_pool = formula_pool;
}

/**
 * @brief Выполняет один цикл работы Лоба-Решателя.
 */
void omega_solver_lobe_tick(omega_solver_lobe_t* lobe) {
    sigma_task_t task;
    // Пытаемся получить следующую задачу
    if (sigma_get_next_task(lobe->coordinator, &task) == 0) {
        // Если задача получена, обрабатываем ее
        switch (task.type) {
            case TASK_CONTRADICTION: {
                printf("[Solver] Processing CONTRADICTION task %llu between facts %llu and %llu.\n",
                       (unsigned long long)task.id,
                       (unsigned long long)task.data.contradiction.formula_ids[0],
                       (unsigned long long)task.data.contradiction.formula_ids[1]);
                
                // Создаем правило, которое объясняет противоречие
                uint64_t new_rule_id = kf_create_rule_for_contradiction(
                    lobe->formula_pool,
                    task.data.contradiction.formula_ids[0],
                    task.data.contradiction.formula_ids[1]
                );

                if (new_rule_id > 0) {
                    printf("[Solver] Created explanation rule %llu to resolve contradiction.\n", (unsigned long long)new_rule_id);
                } else {
                    printf("[Solver] Failed to create a rule for task %llu.\n", (unsigned long long)task.id);
                }
                
                // Помечаем задачу как выполненную
                sigma_update_task_status(lobe->coordinator, task.id, TASK_STATUS_DONE);
                printf("[Solver] Task %llu marked as DONE.\n", (unsigned long long)task.id);
                break;
            }
            case TASK_INVALID_RULE: {
                printf("[Solver] Processing INVALID_RULE task %llu for rule %llu.\n",
                       (unsigned long long)task.id,
                       (unsigned long long)task.data.invalid_rule.rule_id);
                
                kf_invalidate_rule(lobe->formula_pool, task.data.invalid_rule.rule_id);
                printf("[Solver] Rule %llu invalidated.\n", (unsigned long long)task.data.invalid_rule.rule_id);
                
                sigma_update_task_status(lobe->coordinator, task.id, TASK_STATUS_DONE);
                printf("[Solver] Task %llu marked as DONE.\n", (unsigned long long)task.id);
                break;
            }
        }
    }
    // Если задач нет, ничего не делаем
}
