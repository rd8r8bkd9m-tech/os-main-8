SHELL := /bin/bash

.PHONY: build test wasm frontend iso ci clean

build:
	cmake -S . -B build -G Ninja
	cmake --build build

test: build
	ctest --test-dir build
	pytest -q
	ruff check .
	pyright
	npm run test --prefix frontend -- --runInBand

wasm:
	./scripts/build_wasm.sh

frontend: wasm
	npm install --prefix frontend
	npm run build --prefix frontend

iso:
	./scripts/build_iso.sh

ci: build test frontend iso
	python3 scripts/generate_test_dialogs.py --backend stub --output logs/ci_dialogs.json --seed 2025 --count 4
	./scripts/policy_validate.py

clean:
	rm -rf build frontend/dist frontend/node_modules

.PHONY: test-omega
test-omega:
	@echo "--- Building and Running Kolibri-Omega Phase 10 Test ---"
	@mkdir -p build
	$(CC) -o build/cognition_test \
		kolibri_omega/src/canvas.c \
		kolibri_omega/src/observer.c \
		kolibri_omega/src/dreamer.c \
		kolibri_omega/src/sandbox.c \
		kolibri_omega/src/pattern_detector.c \
		kolibri_omega/src/extended_pattern_detector.c \
		kolibri_omega/src/hierarchical_abstraction.c \
		kolibri_omega/src/agent_coordinator.c \
		kolibri_omega/src/counterfactual_reasoner.c \
		kolibri_omega/src/adaptive_abstraction_manager.c \
		kolibri_omega/src/policy_learner.c \
		kolibri_omega/src/bayesian_causal_networks.c \
		kolibri_omega/src/scenario_planner.c \
		kolibri_omega/src/learning_engine.c \
		kolibri_omega/src/inference_engine.c \
		kolibri_omega/src/abstraction_engine.c \
		kolibri_omega/src/self_reflection.c \
		kolibri_omega/src/omega_errors.c \
		kolibri_omega/src/omega_perf.c \
		kolibri_omega/stubs/kf_pool_stub.c \
		kolibri_omega/stubs/sigma_coordinator_stub.c \
		kolibri_omega/src/solver_lobe.c \
		kolibri_omega/src/predictor_lobe.c \
		kolibri_omega/tests/first_cognition.c \
		-I. -pthread -g -lm
	@echo "\n--- Starting Test ---"
	@./build/cognition_test
