"""Energy-aware scheduler for model selection and runner routing.

Implements baseline heuristics for choosing among available inference backends
(local script, persistent runner, upstream LLM) based on energy budget, latency
requirements, and availability.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

__all__ = [
    "RunnerChoice",
    "EnergyAwareScheduler",
]


@dataclass(frozen=True)
class RunnerChoice:
    """Decision returned by the scheduler."""

    runner_type: Literal["script", "local", "upstream"]
    """Type of runner: 'script' (KolibriScript), 'local' (persistent runner), 'upstream' (LLM API)."""

    estimated_cost_j: float
    """Estimated energy cost in joules."""

    estimated_latency_ms: float
    """Estimated latency in milliseconds."""

    reason: str
    """Human-readable reason for this choice."""

    metadata: Dict[str, object]
    """Additional metadata (runner address, model, etc.)."""


class EnergyAwareScheduler:
    """Baseline energy-aware scheduler for inference request routing.

    Uses heuristics to choose between available runners based on:
    - Energy budget constraints (device-specific)
    - Latency SLOs (per-request or global)
    - Availability and health of runners
    - Content complexity (estimated from prompt)
    """

    def __init__(
        self,
        *,
        device_power_budget_j: float = 10.0,
        default_latency_slo_ms: float = 1000.0,
        local_runner_available: bool = False,
        upstream_available: bool = False,
    ) -> None:
        """Initialize scheduler.

        Args:
            device_power_budget_j: Power budget in joules (e.g., battery capacity slice).
            default_latency_slo_ms: Default SLO for latency in milliseconds.
            local_runner_available: Whether persistent local runner is available.
            upstream_available: Whether upstream LLM API is available.
        """
        self.device_power_budget_j = device_power_budget_j
        self.default_latency_slo_ms = default_latency_slo_ms
        self.local_runner_available = local_runner_available
        self.upstream_available = upstream_available

    def _estimate_complexity(self, prompt: str) -> float:
        """Estimate prompt complexity (0.0 to 1.0) based on length and special markers."""
        base = min(len(prompt) / 500.0, 1.0)  # Normalize by typical prompt length
        has_code = "```" in prompt or "def " in prompt or "class " in prompt
        has_math = "$" in prompt or "∑" in prompt or "∫" in prompt
        complexity = base
        if has_code:
            complexity += 0.2
        if has_math:
            complexity += 0.1
        return min(complexity, 1.0)

    def _estimate_script_cost(self, prompt: str) -> tuple[float, float]:
        """Estimate energy and latency for KolibriScript execution.

        Returns:
            (estimated_cost_j, estimated_latency_ms)
        """
        complexity = self._estimate_complexity(prompt)
        # KolibriScript is lightweight: ~0.05 J for simple, ~0.15 J for complex
        cost_j = 0.05 + (complexity * 0.10)
        # Latency ranges from 50ms to 300ms depending on complexity
        latency_ms = 50.0 + (complexity * 250.0)
        return cost_j, latency_ms

    def _estimate_local_cost(self, prompt: str) -> tuple[float, float]:
        """Estimate energy and latency for local persistent runner.

        Returns:
            (estimated_cost_j, estimated_latency_ms)
        """
        complexity = self._estimate_complexity(prompt)
        # Local runner is more powerful: ~0.2 J baseline + load-dependent
        cost_j = 0.2 + (complexity * 0.3)
        # Latency: 200ms baseline + complexity
        latency_ms = 200.0 + (complexity * 400.0)
        return cost_j, latency_ms

    def _estimate_upstream_cost(self, prompt: str) -> tuple[float, float]:
        """Estimate energy and latency for upstream LLM API.

        Returns:
            (estimated_cost_j, estimated_latency_ms)
        """
        complexity = self._estimate_complexity(prompt)
        # Upstream: mostly network + I/O cost ~0.1 J + server-side ~0.5-2 J
        # We estimate conservatively
        cost_j = 0.1 + (complexity * 2.0)
        # Latency: 500ms baseline + network jitter + server processing
        latency_ms = 500.0 + (complexity * 1500.0)
        return cost_j, latency_ms

    def schedule(
        self,
        prompt: str,
        *,
        energy_budget_override_j: Optional[float] = None,
        latency_slo_override_ms: Optional[float] = None,
        prefer_local: bool = False,
    ) -> RunnerChoice:
        """Schedule a request to the best available runner.

        Args:
            prompt: User prompt to process.
            energy_budget_override_j: Override device energy budget for this request.
            latency_slo_override_ms: Override latency SLO for this request.
            prefer_local: If True, prefer local runner when within budgets.

        Returns:
            RunnerChoice with selected runner and rationale.
        """
        energy_budget = energy_budget_override_j or self.device_power_budget_j
        latency_slo = latency_slo_override_ms or self.default_latency_slo_ms

        script_cost, script_lat = self._estimate_script_cost(prompt)
        local_cost, local_lat = self._estimate_local_cost(prompt)
        upstream_cost, upstream_lat = self._estimate_upstream_cost(prompt)

        candidates: List[tuple[str, float, float, str]] = [
            ("script", script_cost, script_lat, "KolibriScript (lightweight deterministic)"),
        ]

        if self.local_runner_available:
            candidates.append(("local", local_cost, local_lat, "Local persistent runner"))

        if self.upstream_available:
            candidates.append(("upstream", upstream_cost, upstream_lat, "Upstream LLM API"))

        # Filter by constraints
        feasible = [
            (runner, cost, lat, desc)
            for runner, cost, lat, desc in candidates
            if cost <= energy_budget and lat <= latency_slo
        ]

        if not feasible:
            # Fallback: choose the one that exceeds budget least
            runner, cost, lat, desc = min(candidates, key=lambda x: x[1])
            return RunnerChoice(
                runner_type=runner,  # type: ignore
                estimated_cost_j=cost,
                estimated_latency_ms=lat,
                reason=f"No option within budget; chose {desc} (budget exceeded: cost {cost:.2f}J vs {energy_budget:.2f}J)",
                metadata={"fallback": True},
            )

        # Choose best candidate among feasible ones
        if prefer_local and any(r[0] == "local" for r in feasible):
            best = next(r for r in feasible if r[0] == "local")
        else:
            # Prefer minimal cost (energy efficiency)
            best = min(feasible, key=lambda x: x[1])

        runner, cost, lat, desc = best
        return RunnerChoice(
            runner_type=runner,  # type: ignore
            estimated_cost_j=cost,
            estimated_latency_ms=lat,
            reason=f"Selected {desc} (cost {cost:.2f}J, latency {lat:.0f}ms)",
            metadata={"energy_budget_j": energy_budget, "latency_slo_ms": latency_slo},
        )

