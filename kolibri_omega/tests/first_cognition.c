#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <string.h>

// Сначала включаем все определения типов
#include "kolibri_omega/include/types.h"
#include "kolibri_omega/include/omega_errors.h"
#include "kolibri_omega/include/omega_perf.h"

// Затем включаем все заголовочные файлы модулей
#include "kolibri_omega/include/canvas.h"
#include "kolibri_omega/include/observer.h"
#include "kolibri_omega/include/dreamer.h"
#include "kolibri_omega/include/sandbox.h"
#include "kolibri_omega/include/solver_lobe.h"
#include "kolibri_omega/include/predictor_lobe.h"
#include "kolibri_omega/include/self_reflection.h"
#include "kolibri_omega/stubs/kf_pool_stub.h"
#include "kolibri_omega/stubs/sigma_coordinator_stub.h"
#include "kolibri_omega/include/extended_pattern_detector.h"
#include "kolibri_omega/include/hierarchical_abstraction.h"
#include "kolibri_omega/include/agent_coordinator.h"
#include "kolibri_omega/include/counterfactual_reasoner.h"
#include "kolibri_omega/include/adaptive_abstraction_manager.h"
#include "kolibri_omega/include/policy_learner.h"
#include "kolibri_omega/include/bayesian_causal_networks.h"
#include "kolibri_omega/include/scenario_planner.h"

int main() {
    srandom(time(NULL));

    // Initialize error handling system first
    int err = omega_error_system_init();
    if (err != OMEGA_OK) {
        fprintf(stderr, "Failed to initialize error system: %d\n", err);
        return 1;
    }
    printf("[ErrorSystem] Initialized successfully\n");
    
    // Initialize performance profiling system
    err = omega_perf_init();
    if (err != OMEGA_OK) {
        fprintf(stderr, "Failed to initialize performance system: %d\n", err);
        return 1;
    }
    printf("[PerfSystem] Initialized successfully\n");

    // Инициализация
    kf_pool_t pool;
    sigma_coordinator_t coord;
    omega_canvas_t canvas;
    omega_observer_t observer;
    omega_dreamer_t dreamer;
    omega_solver_lobe_t solver;
    omega_predictor_lobe_t predictor;
    sandbox_world_t world;

    kf_pool_init(&pool);
    sigma_coordinator_init(&coord);
    omega_canvas_init(&canvas, &pool);
    omega_observer_init(&observer, &canvas, &coord);
    omega_dreamer_init(&dreamer, &canvas, &pool, &coord);
    omega_solver_lobe_init(&solver, &coord, &pool);
    omega_predictor_lobe_init(&predictor, &canvas, &pool);
    omega_self_reflection_init();  // НОВОЕ: инициализирует самоанализ
    omega_extended_pattern_detector_init();  // Phase 3: инициализирует детектор паттернов
    omega_hierarchical_abstraction_init();  // Phase 4: инициализирует иерархию абстракции
    omega_agent_coordinator_init();  // Phase 5: инициализирует координатор агентов
    omega_counterfactual_reasoner_init();  // Phase 6: инициализирует counterfactual reasoner
    omega_adaptive_abstraction_init();  // Phase 7: инициализирует адаптивное абстрактирование
    omega_policy_learner_init();  // Phase 8: инициализирует обучение политикам
    
    // Phase 7: Регистрируем метрики для адаптации
    omega_register_abstraction_metric(OMEGA_METRIC_DIVERGENCE, 0.05, 0.15, 0.5);
    omega_register_abstraction_metric(OMEGA_METRIC_COMPLEXITY, 50.0, 200.0, 0.3);
    omega_register_abstraction_metric(OMEGA_METRIC_SYNCHRONIZATION, 0.3, 0.9, 0.2);
    
    // Устанавливаем начальные значения метрик (норма, внутри диапазонов)
    omega_update_metric(OMEGA_METRIC_DIVERGENCE, 0.10);
    omega_update_metric(OMEGA_METRIC_COMPLEXITY, 120.0);
    omega_update_metric(OMEGA_METRIC_SYNCHRONIZATION, 0.6);
    
    // Phase 8: Создаем начальные политики для ключевых состояний
    omega_create_policy(OMEGA_STATE_STABLE, "stable_policy", 0.1);
    omega_create_policy(OMEGA_STATE_DIVERGING, "diverging_policy", 0.3);
    
    // Phase 9: Инициализируем Байесовскую причинную сеть
    omega_bayesian_network_init();
    
    // Создаем узлы: Divergence, Complexity, SyncState, CoordinationLevel
    const char* divergence_states[] = {"Low", "Medium", "High"};
    uint32_t div_node = omega_add_causal_node("Divergence", 3, divergence_states, 0.33);
    
    const char* complexity_states[] = {"Simple", "Moderate", "Complex"};
    uint32_t complex_node = omega_add_causal_node("Complexity", 3, complexity_states, 0.33);
    
    const char* sync_states[] = {"Synced", "Drift", "Desync"};
    uint32_t sync_node = omega_add_causal_node("Synchronization", 3, sync_states, 0.33);
    
    // Создаем причинные ребра с default CPD (identity matrix)
    omega_add_causal_edge(complex_node, div_node, NULL, 0.75);
    omega_add_causal_edge(div_node, sync_node, NULL, 0.80);
    
    // Phase 10: Инициализируем планировщик сценариев
    omega_scenario_planner_init();
    
    sandbox_init(&world, 2);
    world.objects[0].y = 1.5f;
    world.objects[1].y = 2.5f;

    // Основной цикл симуляции
    for (int t = 0; t < 10; ++t) {
        printf("\n--- Simulation Time: %d ---\n", t);

        // 1. Мир изменяется
        sandbox_update(&world);

        // 2. Наблюдатель видит мир и создает факты
        sandbox_observe_world(&world, &canvas, t);

        // 3. Наблюдатель анализирует холст
        omega_observer_tick(&observer);

        // 4. Предсказатель делает предсказания (с профилированием)
        omega_perf_handle_t perf_pred = omega_perf_start(OMEGA_PERF_INFERENCE);
        omega_predictor_lobe_tick(&predictor, t);
        omega_perf_end(perf_pred);
        
        // Phase 3: Обнаруживаем паттерны из 3+ шагов (с профилированием)
        omega_perf_handle_t perf_pattern = omega_perf_start(OMEGA_PERF_PATTERN_DETECTION);
        omega_detect_extended_patterns(NULL, 5, t * 100);
        omega_perf_end(perf_pattern);

        // 5. Решатель обрабатывает задачи
        omega_solver_lobe_tick(&solver);
        
        // 6. Мечтатель делает свое дело
        omega_dreamer_tick(&dreamer, t);
        
        // 7. НОВОЕ: Каждые 5 тактов выполняем самоанализ
        if (t > 0 && t % 5 == 0) {
            omega_full_self_reflection(&pool);
        }
        
        // Phase 5: Обнаруживаем координацию агентов
        omega_detect_agent_state_changes(1 + (t % 2), 100 + t, t * 100, 0.8 + (t * 0.01));
        omega_find_synchronized_agents(50);  // Поиск синхронных агентов в окне 50ms
        
        // Phase 6: Counterfactual analysis (каждые 3 такта)
        if (t > 0 && t % 3 == 0) {
            uint64_t scenario_id = omega_create_scenario("scenario_hypothesis", t * 100);
            if (scenario_id > 0) {
                omega_add_intervention(scenario_id, OMEGA_INTERVENTION_FORCE_ACTION, 1, 100 + t, 0.7, "Test intervention");
                omega_analyze_scenario_branch(scenario_id, 1);
                omega_apply_interventions(scenario_id);
                omega_detect_causal_links(scenario_id);
                double divergence = omega_compute_divergence(scenario_id);
                
                // Phase 7: Обновляем метрики адаптации
                omega_update_metric(OMEGA_METRIC_DIVERGENCE, divergence);
                omega_update_metric(OMEGA_METRIC_COMPLEXITY, 100.0 + (t * 10.0));
                omega_update_metric(OMEGA_METRIC_SYNCHRONIZATION, 0.5 + (t * 0.05));
                
                // Phase 8: Рекордим эпизод обучения и обновляем политику
                double reward = omega_compute_reward(0.15, divergence, 1, 0.05);
                omega_record_learning_episode(OMEGA_STATE_DIVERGING, scenario_id, reward, OMEGA_STATE_STABLE, divergence);
                omega_update_policy(OMEGA_STATE_DIVERGING, scenario_id, reward, OMEGA_STATE_STABLE);
            }
        }
        
        // Phase 7: Адаптация уровней абстракции (каждые 4 такта)
        if (t > 0 && t % 4 == 0) {
            // Принудительно устанавливаем экстремальные метрики для демонстрации
            if (t == 4) {
                omega_update_metric(OMEGA_METRIC_COMPLEXITY, 250.0);  // Выше верхнего порога
            } else if (t == 8) {
                omega_update_metric(OMEGA_METRIC_COMPLEXITY, 400.0);   // Еще выше
            }
            
            omega_abstraction_level_t new_level = omega_compute_adaptation_level();
            omega_apply_adaptation(new_level);
        }
        
        // Phase 9: Байесовский причинный вывод (каждые 5 тактов)
        if (t > 0 && t % 5 == 0) {
            // Устанавливаем свидетельство о сложности системы
            int complexity_state = (t / 5) % 3;  // Циклируем через 0, 1, 2
            omega_set_evidence(complex_node, complexity_state);
            
            // Выполняем вероятностный вывод для узла Divergence
            omega_inference_result_t divergence_inference;
            omega_bayesian_inference(div_node, &divergence_inference);
            
            // Выполняем вероятностный вывод для узла Synchronization
            omega_inference_result_t sync_inference;
            omega_bayesian_inference(sync_node, &sync_inference);
            
            // Записываем наблюдение для обучения CPD
            uint32_t obs_nodes[] = {complex_node, div_node, sync_node};
            int obs_states[] = {complexity_state, divergence_inference.most_likely_state, sync_inference.most_likely_state};
            double likelihood = divergence_inference.most_likely_probability * sync_inference.most_likely_probability;
            omega_record_causal_observation(obs_nodes, obs_states, 3, likelihood);
            
            // Обновляем CPD на основе накопленных эпизодов
            if (t >= 5) {  // После первого цикла
                omega_learn_cpd_from_episodes();
            }
        }
        
        // Phase 10: Планирование сценариев (каждые 6 тактов)
        if (t > 0 && t % 6 == 0) {
            // Создаем текущее состояние для планирования
            omega_plan_state_t current_state = {
                .state_id = 12000 + t,
                .depth = 0,
                .divergence = 0.1,
                .complexity = 0.5,
                .synchronization = 0.7,
                .coordination_level = 0.6,
                .quality_score = 0.75,
                .is_goal_state = 0
            };
            
            // Создаем план
            uint32_t plan_id = omega_create_scenario_plan("tactical_plan", &current_state, 3);
            
            if (plan_id > 0) {
                // Расширяем дерево сценариев
                omega_expand_scenario_tree(plan_id);
                
                // Вычисляем траекторию к целевому состоянию
                omega_plan_state_t target_state = {
                    .divergence = 0.05,
                    .complexity = 0.3,
                    .synchronization = 0.9,
                    .quality_score = 0.85
                };
                
                // Получаем корневую ветвь (текущее состояние)
                uint32_t root_branch = 0;
                
                omega_compute_trajectory(plan_id, root_branch, &target_state, 5);
                
                // Выбираем лучшую ветвь по expected value
                uint32_t best_branch = omega_select_best_branch(plan_id);
                
                // Предсказываем результат
                omega_plan_outcome_t outcome;
                omega_predict_outcome(plan_id, best_branch, &outcome);
                
                // Симулируем выполнение плана
                omega_plan_trajectory_t trajectory;
                omega_simulate_plan_execution(plan_id, &trajectory);
            }
        }

        omega_canvas_print(&canvas);

        usleep(100000); // Замедлим симуляцию
    }

    // Остановка и уничтожение
    printf("\n--- Simulation Finished. Shutting down. ---\n");
    
    // Print performance report before shutdown
    omega_perf_print_report();
    
    omega_agent_coordinator_shutdown();  // Phase 5: остановка координатора
    omega_counterfactual_reasoner_shutdown();  // Phase 6: остановка counterfactual reasoner
    omega_adaptive_abstraction_shutdown();  // Phase 7: остановка адаптивной абстракции
    omega_policy_learner_shutdown();  // Phase 8: остановка обучения политики
    omega_bayesian_network_shutdown();  // Phase 9: остановка байесовской сети
    omega_scenario_planner_shutdown();  // Phase 10: остановка планировщика
    omega_observer_destroy(&observer);
    omega_dreamer_destroy(&dreamer);
    omega_canvas_destroy(&canvas);
    kf_pool_destroy(&pool);
    sigma_coordinator_destroy(&coord);
    
    // Shutdown profiling and error handling systems last
    omega_perf_shutdown();
    printf("[PerfSystem] Shutdown complete\n");
    omega_error_system_shutdown();
    printf("[ErrorSystem] Shutdown complete\n");

    printf("Shutdown complete.\n");

    return 0;
}
