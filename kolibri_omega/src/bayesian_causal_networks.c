#include "kolibri_omega/include/bayesian_causal_networks.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

typedef struct {
    omega_causal_node_t nodes[OMEGA_MAX_CAUSAL_NODES];
    int node_count;
    
    omega_causal_edge_t edges[OMEGA_MAX_CAUSAL_EDGES];
    int edge_count;
    
    omega_causal_episode_t episodes[OMEGA_MAX_CAUSAL_EPISODES];
    int episode_count;
    
    omega_bayesian_network_stats_t stats;
} omega_bayesian_ctx_t;

static omega_bayesian_ctx_t bayesian_ctx = {0};

/**
 * omega_bayesian_network_init - инициализация
 */
int omega_bayesian_network_init(void) {
    memset(&bayesian_ctx, 0, sizeof(bayesian_ctx));
    
    printf("[BayesianCausal] Initialized with max %d nodes, %d edges\n",
           OMEGA_MAX_CAUSAL_NODES, OMEGA_MAX_CAUSAL_EDGES);
    printf("[BayesianCausal] Probabilistic causality inference enabled\n");
    
    return 0;
}

/**
 * omega_add_causal_node - добавить узел
 */
uint32_t omega_add_causal_node(const char* node_name,
                              int num_states,
                              const char** state_names,
                              double prior_probability) {
    if (bayesian_ctx.node_count >= OMEGA_MAX_CAUSAL_NODES) {
        return 0;
    }
    
    omega_causal_node_t* node = &bayesian_ctx.nodes[bayesian_ctx.node_count];
    
    node->node_id = 5000 + bayesian_ctx.node_count;
    strncpy(node->node_name, node_name, sizeof(node->node_name) - 1);
    node->num_states = num_states;
    
    for (int i = 0; i < num_states && i < OMEGA_MAX_CPD_STATES; i++) {
        strncpy(node->state_names[i], state_names[i], sizeof(node->state_names[i]) - 1);
        node->state_probabilities[i] = 1.0 / num_states;  // Uniform initially
    }
    
    node->prior_probability = prior_probability;
    node->posterior_probability = prior_probability;
    node->observed_state = -1;  // Not observed
    node->is_observed = 0;
    
    bayesian_ctx.node_count++;
    bayesian_ctx.stats.total_nodes++;
    
    printf("[BayesianCausal] Added node %u: \"%s\" with %d states, prior=%.2f\n",
           node->node_id, node_name, num_states, prior_probability);
    
    return node->node_id;
}

/**
 * omega_add_causal_edge - добавить причинное ребро
 */
uint32_t omega_add_causal_edge(uint32_t parent_node_id,
                              uint32_t child_node_id,
                              double** cpd_table,
                              double causal_strength) {
    if (bayesian_ctx.edge_count >= OMEGA_MAX_CAUSAL_EDGES) {
        return 0;
    }
    
    omega_causal_edge_t* edge = &bayesian_ctx.edges[bayesian_ctx.edge_count];
    
    edge->edge_id = 6000 + bayesian_ctx.edge_count;
    edge->parent_node_id = parent_node_id;
    edge->child_node_id = child_node_id;
    edge->causal_strength = causal_strength;
    edge->confirmed = 0;
    edge->times_observed = 0;
    
    // Копируем CPD таблицу
    if (cpd_table) {
        for (int i = 0; i < OMEGA_MAX_CPD_STATES; i++) {
            for (int j = 0; j < OMEGA_MAX_CPD_STATES; j++) {
                edge->cpd[i][j] = cpd_table[i][j];
            }
        }
    } else {
        // Default: identity matrix (максимальная зависимость)
        for (int i = 0; i < OMEGA_MAX_CPD_STATES; i++) {
            for (int j = 0; j < OMEGA_MAX_CPD_STATES; j++) {
                edge->cpd[i][j] = (i == j) ? 0.9 : 0.1 / (OMEGA_MAX_CPD_STATES - 1);
            }
        }
    }
    
    bayesian_ctx.edge_count++;
    bayesian_ctx.stats.total_edges++;
    bayesian_ctx.stats.average_causal_strength += causal_strength;
    
    printf("[BayesianCausal] Added edge %u: %u -> %u (strength=%.2f)\n",
           edge->edge_id, parent_node_id, child_node_id, causal_strength);
    
    return edge->edge_id;
}

/**
 * omega_set_evidence - установить свидетельство
 */
int omega_set_evidence(uint32_t node_id, int observed_state) {
    for (int i = 0; i < bayesian_ctx.node_count; i++) {
        if (bayesian_ctx.nodes[i].node_id == node_id) {
            bayesian_ctx.nodes[i].is_observed = 1;
            bayesian_ctx.nodes[i].observed_state = observed_state;
            
            printf("[BayesianCausal] Set evidence: Node %u = state %d\n",
                   node_id, observed_state);
            
            return 0;
        }
    }
    return -1;
}

/**
 * omega_bayesian_inference - вероятностный вывод
 * 
 * Использует простой Байесовский вывод:
 * P(X | E) ∝ P(E | X) * P(X)
 */
int omega_bayesian_inference(uint32_t target_node_id,
                            omega_inference_result_t* result_out) {
    if (!result_out) {
        return -1;
    }
    
    // Найти целевой узел
    omega_causal_node_t* target = NULL;
    for (int i = 0; i < bayesian_ctx.node_count; i++) {
        if (bayesian_ctx.nodes[i].node_id == target_node_id) {
            target = &bayesian_ctx.nodes[i];
            break;
        }
    }
    
    if (!target) {
        return -1;
    }
    
    result_out->node_id = target_node_id;
    
    // Вычисляем posterior для каждого состояния целевого узла
    double likelihood[OMEGA_MAX_CPD_STATES];
    memset(likelihood, 0, sizeof(likelihood));
    
    // P(Evidence | State) оценивается из родительских узлов
    for (int state = 0; state < target->num_states; state++) {
        likelihood[state] = target->state_probabilities[state];
        
        // Применяем свидетельство: если узел наблюдается, вероятность = 1 для этого состояния
        if (target->is_observed) {
            if (target->observed_state == state) {
                likelihood[state] = 1.0;
            } else {
                likelihood[state] = 0.0;
            }
        } else {
            // Иначе: пропагируем вероятность через родительские узлы
            // (упрощенный вывод)
            for (int e = 0; e < bayesian_ctx.edge_count; e++) {
                if (bayesian_ctx.edges[e].child_node_id == target_node_id) {
                    // Есть ребро от parent к нам
                    omega_causal_edge_t* edge = &bayesian_ctx.edges[e];
                    
                    // Найти родителя
                    for (int p = 0; p < bayesian_ctx.node_count; p++) {
                        if (bayesian_ctx.nodes[p].node_id == edge->parent_node_id) {
                            omega_causal_node_t* parent = &bayesian_ctx.nodes[p];
                            
                            // P(target=state | parent_state) из CPD
                            if (parent->is_observed) {
                                double conditional = edge->cpd[parent->observed_state][state];
                                likelihood[state] *= conditional;
                            }
                            break;
                        }
                    }
                }
            }
        }
    }
    
    // Нормализуем posterior: P(X|E) = P(E|X)*P(X) / P(E)
    double total_likelihood = 0.0;
    for (int i = 0; i < target->num_states; i++) {
        total_likelihood += likelihood[i];
    }
    
    if (total_likelihood > 0.0) {
        for (int i = 0; i < target->num_states; i++) {
            result_out->posterior[i] = likelihood[i] / total_likelihood;
        }
    }
    
    // Найти наиболее вероятное состояние
    result_out->most_likely_state = 0;
    result_out->most_likely_probability = result_out->posterior[0];
    
    for (int i = 1; i < target->num_states; i++) {
        if (result_out->posterior[i] > result_out->most_likely_probability) {
            result_out->most_likely_probability = result_out->posterior[i];
            result_out->most_likely_state = i;
        }
    }
    
    // Вычисляем энтропию: H(X) = -Σ P(x) * log(P(x))
    result_out->entropy = 0.0;
    for (int i = 0; i < target->num_states; i++) {
        if (result_out->posterior[i] > 1e-10) {
            result_out->entropy -= result_out->posterior[i] * log(result_out->posterior[i]);
        }
    }
    
    bayesian_ctx.stats.total_inferences++;
    bayesian_ctx.stats.average_entropy += result_out->entropy;
    
    printf("[BayesianCausal] Inference for node %u: state=%d, prob=%.2f, entropy=%.3f\n",
           target_node_id, result_out->most_likely_state,
           result_out->most_likely_probability, result_out->entropy);
    
    return 0;
}

/**
 * omega_record_causal_observation - записать наблюдение
 */
int omega_record_causal_observation(const uint32_t* node_ids,
                                   const int* states,
                                   int num_observations,
                                   double likelihood) {
    if (bayesian_ctx.episode_count >= OMEGA_MAX_CAUSAL_EPISODES) {
        return -1;
    }
    
    omega_causal_episode_t* episode = &bayesian_ctx.episodes[bayesian_ctx.episode_count];
    
    episode->episode_id = 7000 + bayesian_ctx.episode_count;
    episode->timestamp_ms = 0;  // Placeholder
    episode->num_observations = num_observations;
    episode->likelihood = likelihood;
    
    for (int i = 0; i < num_observations && i < OMEGA_MAX_CAUSAL_NODES; i++) {
        episode->node_ids[i] = node_ids[i];
        episode->observed_states[i] = states[i];
    }
    
    bayesian_ctx.episode_count++;
    bayesian_ctx.stats.total_learning_episodes++;
    bayesian_ctx.stats.total_likelihood += likelihood;
    
    return 0;
}

/**
 * omega_learn_cpd_from_episodes - обновить CPD
 */
int omega_learn_cpd_from_episodes(void) {
    if (bayesian_ctx.episode_count == 0) {
        return 0;
    }
    
    // Для каждого ребра: обновить CPD на основе наблюдений
    for (int e = 0; e < bayesian_ctx.edge_count; e++) {
        omega_causal_edge_t* edge = &bayesian_ctx.edges[e];
        
        // Считаем совместные вероятности из эпизодов
        int joint_counts[OMEGA_MAX_CPD_STATES][OMEGA_MAX_CPD_STATES];
        memset(joint_counts, 0, sizeof(joint_counts));
        
        for (int ep = 0; ep < bayesian_ctx.episode_count; ep++) {
            omega_causal_episode_t* episode = &bayesian_ctx.episodes[ep];
            
            // Найти состояния parent и child в этом эпизоде
            int parent_state = -1, child_state = -1;
            
            for (int o = 0; o < episode->num_observations; o++) {
                if (episode->node_ids[o] == edge->parent_node_id) {
                    parent_state = episode->observed_states[o];
                }
                if (episode->node_ids[o] == edge->child_node_id) {
                    child_state = episode->observed_states[o];
                }
            }
            
            if (parent_state >= 0 && child_state >= 0 && parent_state < OMEGA_MAX_CPD_STATES && child_state < OMEGA_MAX_CPD_STATES) {
                joint_counts[parent_state][child_state]++;
            }
        }
        
        // Обновляем CPD с использованием Байесовского обновления
        for (int p = 0; p < OMEGA_MAX_CPD_STATES; p++) {
            double row_sum = 0.0;
            for (int c = 0; c < OMEGA_MAX_CPD_STATES; c++) {
                row_sum += joint_counts[p][c];
            }
            
            if (row_sum > 0.0) {
                for (int c = 0; c < OMEGA_MAX_CPD_STATES; c++) {
                    // Лапласово сглаживание: (count + 1) / (total + K)
                    edge->cpd[p][c] = (joint_counts[p][c] + 1.0) / (row_sum + OMEGA_MAX_CPD_STATES);
                    edge->times_observed++;
                }
            }
        }
        
        // Если CPD достаточно уверен, помечаем ребро как подтвержденное
        if (edge->times_observed > 5 && edge->causal_strength > 0.6) {
            edge->confirmed = 1;
            bayesian_ctx.stats.confirmed_causal_edges++;
        }
    }
    
    printf("[BayesianCausal] Learned CPD from %d episodes\n",
           bayesian_ctx.episode_count);
    
    return 0;
}

/**
 * omega_find_markov_blanket - найти Markov Blanket
 */
int omega_find_markov_blanket(uint32_t node_id,
                             uint32_t* blanket_nodes_out,
                             int* blanket_size_out) {
    if (!blanket_nodes_out || !blanket_size_out) {
        return -1;
    }
    
    int blanket_size = 0;
    
    // Найти всех родителей
    for (int e = 0; e < bayesian_ctx.edge_count; e++) {
        if (bayesian_ctx.edges[e].child_node_id == node_id) {
            blanket_nodes_out[blanket_size++] = bayesian_ctx.edges[e].parent_node_id;
        }
    }
    
    // Найти всех детей
    for (int e = 0; e < bayesian_ctx.edge_count; e++) {
        if (bayesian_ctx.edges[e].parent_node_id == node_id) {
            blanket_nodes_out[blanket_size++] = bayesian_ctx.edges[e].child_node_id;
        }
    }
    
    // Найти со-родителей (родителей детей)
    for (int e = 0; e < bayesian_ctx.edge_count; e++) {
        if (bayesian_ctx.edges[e].parent_node_id == node_id) {
            uint32_t child = bayesian_ctx.edges[e].child_node_id;
            
            // Найти других родителей этого ребенка
            for (int e2 = 0; e2 < bayesian_ctx.edge_count; e2++) {
                if (bayesian_ctx.edges[e2].child_node_id == child &&
                    bayesian_ctx.edges[e2].parent_node_id != node_id) {
                    blanket_nodes_out[blanket_size++] = bayesian_ctx.edges[e2].parent_node_id;
                }
            }
        }
    }
    
    *blanket_size_out = blanket_size;
    
    printf("[BayesianCausal] Markov Blanket for node %u: %d nodes\n",
           node_id, blanket_size);
    
    return 0;
}

/**
 * omega_get_causal_network_statistics - получить статистику
 */
const omega_bayesian_network_stats_t* omega_get_causal_network_statistics(void) {
    if (bayesian_ctx.stats.total_inferences > 0) {
        bayesian_ctx.stats.average_entropy /= bayesian_ctx.stats.total_inferences;
    }
    
    if (bayesian_ctx.stats.total_edges > 0) {
        bayesian_ctx.stats.average_causal_strength /= bayesian_ctx.stats.total_edges;
    }
    
    return &bayesian_ctx.stats;
}

/**
 * omega_bayesian_network_shutdown - остановка
 */
void omega_bayesian_network_shutdown(void) {
    const omega_bayesian_network_stats_t* stats = omega_get_causal_network_statistics();
    
    printf("[BayesianCausal] Shutdown: %d nodes, %d edges, %d inferences\n",
           bayesian_ctx.node_count, bayesian_ctx.edge_count,
           bayesian_ctx.stats.total_inferences);
    printf("  Confirmed causal edges: %d, Rejected: %d\n",
           stats->confirmed_causal_edges, stats->rejected_causal_edges);
    printf("  Average entropy: %.3f, Average causal strength: %.2f\n",
           stats->average_entropy, stats->average_causal_strength);
    printf("  Learning episodes: %d, Total likelihood: %.2f\n",
           stats->total_learning_episodes, stats->total_likelihood);
    
    memset(&bayesian_ctx, 0, sizeof(bayesian_ctx));
}
