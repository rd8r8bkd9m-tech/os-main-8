#ifndef SIGMA_COORDINATOR_STUB_H
#define SIGMA_COORDINATOR_STUB_H

#include "kolibri_omega/include/forward.h"
#include <stdint.h> // для uint64_t

// Функции для работы с координатором задач

void sigma_coordinator_init(sigma_coordinator_t* coordinator);
void sigma_coordinator_destroy(sigma_coordinator_t* coordinator);
int sigma_add_task(sigma_coordinator_t* coordinator, sigma_task_t* task);
int sigma_get_next_task(sigma_coordinator_t* coordinator, sigma_task_t* task);
int sigma_update_task_status(sigma_coordinator_t* coordinator, uint64_t task_id, sigma_task_status_t status);

#endif // SIGMA_COORDINATOR_STUB_H
