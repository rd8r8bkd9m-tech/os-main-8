#ifndef OMEGA_PREDICTOR_LOBE_H
#define OMEGA_PREDICTOR_LOBE_H

#include "kolibri_omega/include/forward.h"

// Функции для работы с долей-предсказателем

void omega_predictor_lobe_init(omega_predictor_lobe_t* lobe, omega_canvas_t* canvas, kf_pool_t* formula_pool);
void omega_predictor_lobe_tick(omega_predictor_lobe_t* lobe, int current_time);

#endif // OMEGA_PREDICTOR_LOBE_H