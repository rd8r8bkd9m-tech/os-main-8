#ifndef OMEGA_OBSERVER_H
#define OMEGA_OBSERVER_H

#include "kolibri_omega/include/forward.h"

// Функции для работы с наблюдателем

int omega_observer_init(omega_observer_t* observer, omega_canvas_t* canvas, sigma_coordinator_t* coordinator);
void omega_observer_tick(omega_observer_t* observer);
void omega_observer_destroy(omega_observer_t* observer);

#endif // OMEGA_OBSERVER_H
