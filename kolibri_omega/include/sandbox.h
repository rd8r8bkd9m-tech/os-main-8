#ifndef OMEGA_SANDBOX_H
#define OMEGA_SANDBOX_H

#include "kolibri_omega/include/forward.h"
#include "kolibri_omega/include/sandbox.h"

/**
 * @brief Инициализирует мир-песочницу.
 * @param world Указатель на структуру мира.
 * @param num_objects Количество объектов в мире.
 */
void sandbox_init(sandbox_world_t* world, size_t num_objects);

/**
 * @brief Обновляет состояние мира-песочницы.
 * 
 * Выполняет один шаг симуляции, обновляя состояние всех объектов
 * в мире (например, объекты падают под действием гравитации).
 * @param world Указатель на мир.
 */
void sandbox_update(sandbox_world_t* world);

/**
 * @brief Наблюдает за миром песочницы.
 * 
 * Позволяет визуализировать или иным образом взаимодействовать
 * с текущим состоянием мира песочницы.
 * @param world Указатель на мир.
 * @param canvas Указатель на холст для рисования.
 * @param time Время, прошедшее с начала симуляции.
 */
void sandbox_observe_world(sandbox_world_t* world, omega_canvas_t* canvas, int time);

#endif // OMEGA_SANDBOX_H
