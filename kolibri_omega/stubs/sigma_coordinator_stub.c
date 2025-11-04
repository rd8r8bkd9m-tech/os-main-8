#include "kolibri_omega/include/types.h"
#include "kolibri_omega/stubs/sigma_coordinator_stub.h"
#include <stdio.h>
#include <string.h>

#include "kolibri_omega/include/types.h"
#include "kolibri_omega/stubs/sigma_coordinator_stub.h"
#include <stdio.h>
#include <string.h>

/**
 * @brief Инициализирует Координатор.
 */
void sigma_coordinator_init(sigma_coordinator_t* coordinator) {
    coordinator->count = 0;
    coordinator->next_task_id = 1;
    coordinator->next_task_to_process = 0;
}

/**
 * @brief Уничтожает Координатор.
 */
void sigma_coordinator_destroy(sigma_coordinator_t* coordinator) {
    // В однопоточной версии здесь делать нечего
}

/**
 * @brief Добавляет новую задачу в очередь Координатора.
 */
int sigma_add_task(sigma_coordinator_t* coordinator, sigma_task_t* task) {
    if (coordinator->count >= MAX_TASKS) {
        return -1; // Очередь полна
    }
    task->id = coordinator->next_task_id++;
    task->status = TASK_STATUS_OPEN;
    coordinator->tasks[coordinator->count++] = *task;
    printf("COORDINATOR: New task added, total tasks: %d\n", coordinator->count);
    return 0;
}

/**
 * @brief Извлекает следующую невыполненную задачу по кругу (round-robin).
 */
int sigma_get_next_task(sigma_coordinator_t* coordinator, sigma_task_t* task) {
    if (coordinator->count == 0) {
        return -1; // Нет задач
    }

    for (size_t i = 0; i < coordinator->count; ++i) {
        size_t current_index = (coordinator->next_task_to_process + i) % coordinator->count;
        
        if (coordinator->tasks[current_index].status == TASK_STATUS_OPEN) {
            coordinator->tasks[current_index].status = TASK_STATUS_IN_PROGRESS;
            *task = coordinator->tasks[current_index];
            // Обновляем индекс для следующего вызова, чтобы не начинать поиск сначала
            coordinator->next_task_to_process = (current_index + 1) % coordinator->count;
            return 0; // Задача найдена
        }
    }

    return -1; // Нет открытых задач
}

/**
 * @brief Обновляет статус задачи.
 */
int sigma_update_task_status(sigma_coordinator_t* coordinator, uint64_t task_id, sigma_task_status_t status) {
    for (int i = 0; i < coordinator->count; ++i) {
        if (coordinator->tasks[i].id == task_id) {
            coordinator->tasks[i].status = status;
            return 0;
        }
    }
    return -1; // Задача не найдена
}

