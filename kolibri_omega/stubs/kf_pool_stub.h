#ifndef KF_POOL_STUB_H
#define KF_POOL_STUB_H

#include "kolibri_omega/include/forward.h"
#include <stdint.h>

// Функции для работы с пулом формул

void kf_pool_init(kf_pool_t* pool);
void kf_pool_destroy(kf_pool_t* pool);
uint64_t kf_add_formula(kf_pool_t* pool, kf_formula_t* formula);
int kf_get_formula(kf_pool_t* pool, uint64_t formula_id, kf_formula_t* formula);
int kf_set_formula(kf_pool_t* pool, uint64_t formula_id, kf_formula_t* formula);
int kf_are_contradictory(kf_pool_t* pool, uint64_t formula_id1, uint64_t formula_id2);
void kf_print_formula(kf_pool_t* pool, uint64_t formula_id);
int kf_invalidate_rule(kf_pool_t* pool, uint64_t rule_id);
uint64_t kf_create_rule_from_facts(kf_pool_t* pool, uint64_t fact_id1, uint64_t fact_id2);
uint64_t kf_create_rule_for_contradiction(kf_pool_t* pool, uint64_t contradicting_fact_id1, uint64_t contradicting_fact_id2);
int kf_apply_rule_to_fact(kf_pool_t* pool, uint64_t rule_id, uint64_t fact_id, kf_formula_t* predicted_formula);

#endif // KF_POOL_STUB_H
