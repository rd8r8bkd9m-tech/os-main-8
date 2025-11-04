#ifndef OMEGA_CANVAS_H
#define OMEGA_CANVAS_H

#include "kolibri_omega/include/forward.h"

/**
 * @brief Инициализирует Холст.
 * @param canvas Указатель на инициализируемый холст.
 * @param formula_pool Указатель на пул формул.
 * @return 0 в случае успеха, -1 в случае ошибки.
 */
int omega_canvas_init(omega_canvas_t* canvas, kf_pool_t* formula_pool);

/**
 * @brief Уничтожает холст, освобождая ресурсы.
 * @param canvas Указатель на структуру Холста.
 */
void omega_canvas_destroy(omega_canvas_t* canvas);

/**
 * @brief Добавляет новый элемент на Холст.
 * @param canvas Указатель на Холст.
 * @param item Указатель на элемент, который нужно добавить.
 * @return ID добавленного элемента или 0 в случае ошибки.
 */
uint64_t omega_canvas_add_item(omega_canvas_t* canvas, omega_canvas_item_t* item);

/**
 * @brief Удаляет элемент с Холста.
 * @param canvas Указатель на Холст.
 * @param index Индекс элемента для удаления.
 * @return 0 в случае успеха, -1 в случае ошибки.
 */
int omega_canvas_remove_item(omega_canvas_t* canvas, size_t index);

/**
 * @brief Находит элемент на Холсте по его ID.
 * @param canvas Указатель на Холст.
 * @param item_id ID искомого элемента.
 * @return Указатель на элемент или NULL, если он не найден.
 */
omega_canvas_item_t* omega_canvas_get_item(omega_canvas_t* canvas, uint64_t item_id);

/**
 * @brief Печатает содержимое Холста (для отладки).
 * @param canvas Указатель на Холст.
 */
void omega_canvas_print(const omega_canvas_t* canvas);


#endif // OMEGA_CANVAS_H
