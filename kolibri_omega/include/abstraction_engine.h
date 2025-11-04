#ifndef OMEGA_ABSTRACTION_ENGINE_H
#define OMEGA_ABSTRACTION_ENGINE_H

#include "kolibri_omega/include/forward.h"
#include <stdint.h>
#include <stddef.h>

/**
 * @brief Модуль абстракции и категоризации.
 * 
 * Позволяет системе группировать похожие факты в категории/классы:
 * - "Объект падает" (группирует все факты о снижении позиции)
 * - "Объект стабилен" (группирует все факты, где позиция неизменна)
 * 
 * Это позволяет создавать более общие правила:
 * - Вместо "если объект 1 в позиции Y1, то объект 2 в позиции Y2"
 * - Становится "если объект FALLING, то другой объект тоже FALLING"
 */

#define MAX_CATEGORIES 32
#define MAX_FACTS_PER_CATEGORY 256

typedef enum {
    CATEGORY_POSITION,
    CATEGORY_MOTION,
    CATEGORY_STATE,
    CATEGORY_RELATIONSHIP
} omega_category_type_t;

/**
 * @brief Структура категории - абстрактного класса фактов.
 */
typedef struct {
    uint64_t id;
    omega_category_type_t type;
    char name[64];                    // "FALLING", "STABLE", "ACCELERATING"
    uint64_t member_facts[MAX_FACTS_PER_CATEGORY];
    size_t member_count;
    double average_confidence;        // Средняя уверенность в факты этой категории
} omega_category_t;

/**
 * @brief Инициализирует модуль абстракции.
 */
void omega_abstraction_engine_init(void);

/**
 * @brief Категоризирует факт - определяет, к какой категории он относится.
 * Возвращает ID категории или 0, если факт не категоризирован.
 */
uint64_t omega_categorize_fact(kf_pool_t* formula_pool, uint64_t fact_id, 
                               omega_category_t* categories, size_t num_categories);

/**
 * @brief Обнаруживает категории в текущем наборе фактов на холсте.
 * Выполняет кластеризацию похожих фактов.
 */
int omega_discover_categories(omega_canvas_t* canvas, kf_pool_t* formula_pool,
                              omega_category_t* categories, size_t max_categories);

/**
 * @brief Создает обобщенное правило на основе категорий вместо конкретных фактов.
 * Это создает более переиспользуемые правила.
 */
uint64_t omega_create_abstract_rule(kf_pool_t* formula_pool,
                                     omega_category_t* condition_category,
                                     omega_category_t* consequence_category);

#endif // OMEGA_ABSTRACTION_ENGINE_H
