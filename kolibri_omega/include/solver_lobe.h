#ifndef OMEGA_SOLVER_LOBE_H
#define OMEGA_SOLVER_LOBE_H

#include "kolibri_omega/include/forward.h"

// Функции для работы с долей-решателем

void omega_solver_lobe_init(omega_solver_lobe_t* lobe, sigma_coordinator_t* coordinator, kf_pool_t* formula_pool);
void omega_solver_lobe_tick(omega_solver_lobe_t* lobe);

#endif // OMEGA_SOLVER_LOBE_H