#ifndef OMEGA_DREAMER_H
#define OMEGA_DREAMER_H

#include "kolibri_omega/include/forward.h"

// Функции для работы с мечтателем

int omega_dreamer_init(omega_dreamer_t* dreamer, omega_canvas_t* canvas, kf_pool_t* formula_pool, sigma_coordinator_t* coordinator);
void omega_dreamer_tick(omega_dreamer_t* dreamer, int current_time);
void omega_dreamer_destroy(omega_dreamer_t* dreamer);

#endif // OMEGA_DREAMER_H
