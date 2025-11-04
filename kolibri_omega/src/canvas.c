#include "kolibri_omega/include/types.h"
#include "kolibri_omega/include/canvas.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/**
 * @brief Инициализирует Холст.
 */
int omega_canvas_init(omega_canvas_t* canvas, kf_pool_t* formula_pool) {
    if (!canvas || !formula_pool) return -1;
    canvas->formula_pool = formula_pool;
    canvas->count = 0;
    canvas->next_item_id = 1;
    // Массив 'items' является частью структуры и не требует динамического выделения
    return 0;
}

/**
 * @brief Уничтожает Холст, освобождая все ресурсы.
 */
void omega_canvas_destroy(omega_canvas_t* canvas) {
    // Нет необходимости освобождать 'items', так как он не выделяется динамически
    if (canvas) {
        canvas->count = 0;
    }
}

/**
 * @brief Добавляет новый элемент на Холст.
 */
uint64_t omega_canvas_add_item(omega_canvas_t* canvas, omega_canvas_item_t* item) {
    if (canvas->count >= MAX_CANVAS_ITEMS) {
        printf("Canvas is full!\n");
        return 0;
    }
    item->id = canvas->next_item_id++;
    canvas->items[canvas->count++] = *item;
    return item->id;
}

/**
 * @brief Удаляет элемент с Холста по индексу.
 */
int omega_canvas_remove_item(omega_canvas_t* canvas, size_t index) {
    if (index >= canvas->count) {
        return -1;
    }
    for (size_t i = index; i < canvas->count - 1; ++i) {
        canvas->items[i] = canvas->items[i + 1];
    }
    canvas->count--;
    return 0;
}

/**
 * @brief Печатает содержимое Холста.
 */
void omega_canvas_print(const omega_canvas_t* canvas) {
    printf("\n--- Canvas State (count: %zu) ---\n", canvas->count);
    for (size_t i = 0; i < canvas->count; ++i) {
        const omega_canvas_item_t* item = &canvas->items[i];
        const char* type_str = item->type == OMEGA_HYPOTHESIS_FACT ? "FACT" : "PREDICTION";
        printf("  [%zu] ID: %llu, Type: %s, FormulaID: %llu, Timestamp: %d\n",
               i, (unsigned long long)item->id, type_str, (unsigned long long)item->formula_id, item->timestamp);
        kf_print_formula(canvas->formula_pool, item->formula_id);
    }
    printf("--- End of Canvas State ---\n\n");
}
