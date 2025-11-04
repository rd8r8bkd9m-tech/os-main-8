#include "kolibri_omega/include/types.h"
#include "kolibri_omega/include/sandbox.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "kolibri_omega/include/canvas.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"

void sandbox_init(sandbox_world_t* world, size_t num_objects) {
    if (num_objects > MAX_OBJECTS) {
        num_objects = MAX_OBJECTS;
    }
    world->num_objects = num_objects;
    world->gravity = -9.8f;
    for (size_t i = 0; i < num_objects; ++i) {
        world->objects[i].id = (int)i + 1;
        world->objects[i].y = 10.0f; // Start high
        world->objects[i].vy = 0.0f;
    }
}

void sandbox_update(sandbox_world_t* world) {
    float dt = 0.1f; // Simulation time step
    for (size_t i = 0; i < world->num_objects; ++i) {
        world->objects[i].vy += world->gravity * dt;
        world->objects[i].y += world->objects[i].vy * dt;
        if (world->objects[i].y < 0) {
            world->objects[i].y = 0;
            world->objects[i].vy = 0;
        }
    }
}

void sandbox_observe_world(sandbox_world_t* world, omega_canvas_t* canvas, int time) {
    printf("[Observer] Observing world at time %d.\n", time);
    // Блокировки мьютексов удалены для однопоточной модели
    for (size_t i = 0; i < world->num_objects; ++i) {
        kf_formula_t fact_formula = {
            .type = KF_TYPE_FACT,
            .is_valid = 1,
            .time = time,
            .data = {
                .fact = {
                    .object_id = world->objects[i].id,
                    .num_predicates = 1
                }
            }
        };
        strcpy(fact_formula.data.fact.predicates[0].name, "position_y");
        snprintf(fact_formula.data.fact.predicates[0].value, sizeof(fact_formula.data.fact.predicates[0].value), "%.2f", world->objects[i].y);

        uint64_t formula_id = kf_add_formula(canvas->formula_pool, &fact_formula);
        if (formula_id > 0) {
            omega_canvas_item_t item = {
                .type = OMEGA_HYPOTHESIS_FACT,
                .formula_id = formula_id,
                .derived_from_rule_id = 0,
                .timestamp = time
            };
            omega_canvas_add_item(canvas, &item);
        }
    }
    // Блокировки мьютексов удалены для однопоточной модели
}
