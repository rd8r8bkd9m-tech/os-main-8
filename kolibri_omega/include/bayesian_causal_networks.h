#ifndef OMEGA_BAYESIAN_CAUSAL_NETWORKS_H
#define OMEGA_BAYESIAN_CAUSAL_NETWORKS_H

#include <stdint.h>

/* ========== Константы ========== */
#define OMEGA_MAX_CAUSAL_NODES 50
#define OMEGA_MAX_CAUSAL_EDGES 200
#define OMEGA_MAX_EVIDENCE_STATES 100
#define OMEGA_MAX_CPD_STATES 10
#define OMEGA_MAX_CAUSAL_EPISODES 500

/* ========== Структуры данных ========== */

/**
 * omega_causal_node_t - узел в Байесовской сети
 * 
 * Представляет переменную в причинной сети
 */
typedef struct {
    uint32_t node_id;
    char node_name[64];
    
    // Вероятностные состояния
    int num_states;
    char state_names[OMEGA_MAX_CPD_STATES][32];
    double state_probabilities[OMEGA_MAX_CPD_STATES];
    
    // Prior probability: P(Node)
    double prior_probability;
    
    // Observed evidence (если есть)
    int observed_state;  // -1 = не наблюдается
    int is_observed;
    
    // Apriori vs Posterior
    double posterior_probability;
} omega_causal_node_t;

/**
 * omega_causal_edge_t - причинное ребро A -> B
 * 
 * Представляет причинную связь между узлами
 */
typedef struct {
    uint32_t edge_id;
    uint32_t parent_node_id;
    uint32_t child_node_id;
    
    // Strength of causality: 0.0 (weak) - 1.0 (strong)
    double causal_strength;
    
    // Conditional Probability Distribution: P(Child=j | Parent=i)
    // cpd[i][j] = P(Child_state_j | Parent_state_i)
    double cpd[OMEGA_MAX_CPD_STATES][OMEGA_MAX_CPD_STATES];
    
    // Learned from data
    int times_observed;
    int confirmed;
} omega_causal_edge_t;

/**
 * omega_cpd_t - Conditional Probability Distribution
 * 
 * Полная условная вероятностная таблица для узла
 */
typedef struct {
    uint32_t node_id;
    
    // Если у узла нет родителей: безусловное распределение
    // Если родители есть: условное распределение
    int num_parents;
    uint32_t parent_ids[5];  // до 5 родителей
    
    // CPD table: prob[parent_combo][node_state]
    // parent_combo кодируется как целое число
    double probability_table[100][OMEGA_MAX_CPD_STATES];
    
    // Граница уверенности для CPD
    double confidence_threshold;
} omega_cpd_t;

/**
 * omega_inference_result_t - результат вероятностного вывода
 */
typedef struct {
    uint32_t node_id;
    
    // Posterior P(Node | Evidence)
    double posterior[OMEGA_MAX_CPD_STATES];
    
    // Наиболее вероятное состояние
    int most_likely_state;
    double most_likely_probability;
    
    // Энтропия: неуверенность в предсказании
    double entropy;
} omega_inference_result_t;

/**
 * omega_causal_episode_t - запись эпизода для обучения
 * 
 * Используется для обновления CPD на основе наблюдений
 */
typedef struct {
    uint32_t episode_id;
    uint64_t timestamp_ms;
    
    // Наблюдаемые состояния узлов
    uint32_t node_ids[OMEGA_MAX_CAUSAL_NODES];
    int observed_states[OMEGA_MAX_CAUSAL_NODES];
    int num_observations;
    
    // Предполагаемые причинные отношения
    int cause_to_effect;  // 1 = причина к следствию подтверждена
    double likelihood;
} omega_causal_episode_t;

/**
 * omega_bayesian_network_stats_t - статистика сети
 */
typedef struct {
    int total_nodes;
    int total_edges;
    int total_inferences;
    int total_learning_episodes;
    
    int confirmed_causal_edges;
    int rejected_causal_edges;
    
    double average_entropy;
    double average_causal_strength;
    double total_likelihood;
    
    int most_influential_node;
} omega_bayesian_network_stats_t;

/* ========== API функции ========== */

/**
 * omega_bayesian_network_init - инициализация системы
 */
int omega_bayesian_network_init(void);

/**
 * omega_add_causal_node - добавить узел в сеть
 */
uint32_t omega_add_causal_node(const char* node_name,
                              int num_states,
                              const char** state_names,
                              double prior_probability);

/**
 * omega_add_causal_edge - добавить причинное ребро A -> B
 * 
 * Использует CPD для кодирования условной вероятности
 */
uint32_t omega_add_causal_edge(uint32_t parent_node_id,
                              uint32_t child_node_id,
                              double** cpd_table,
                              double causal_strength);

/**
 * omega_set_evidence - установить наблюдаемое свидетельство для узла
 */
int omega_set_evidence(uint32_t node_id, int observed_state);

/**
 * omega_bayesian_inference - выполнить вероятностный вывод
 * 
 * Использует алгоритм belief propagation или точного вывода
 * для вычисления P(Node | Evidence) для всех узлов
 */
int omega_bayesian_inference(uint32_t target_node_id,
                            omega_inference_result_t* result_out);

/**
 * omega_record_causal_observation - записать наблюдение для обучения CPD
 */
int omega_record_causal_observation(const uint32_t* node_ids,
                                   const int* states,
                                   int num_observations,
                                   double likelihood);

/**
 * omega_learn_cpd_from_episodes - обновить CPD на основе эпизодов
 * 
 * Байесовское обновление: P(CPD | Data) ∝ P(Data | CPD) * P(CPD)
 */
int omega_learn_cpd_from_episodes(void);

/**
 * omega_find_markov_blanket - найти Markov Blanket узла
 * 
 * Markov Blanket: множество узлов, на которых целевой узел независим от остальных
 * Markov Blanket(X) = Parents(X) ∪ Children(X) ∪ CoParents(X)
 */
int omega_find_markov_blanket(uint32_t node_id,
                             uint32_t* blanket_nodes_out,
                             int* blanket_size_out);

/**
 * omega_get_causal_network_statistics - получить статистику сети
 */
const omega_bayesian_network_stats_t* omega_get_causal_network_statistics(void);

/**
 * omega_bayesian_network_shutdown - остановка
 */
void omega_bayesian_network_shutdown(void);

#endif  // OMEGA_BAYESIAN_CAUSAL_NETWORKS_H
