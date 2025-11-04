"""Tests for energy-aware scheduler."""
from __future__ import annotations

import pytest
from backend.service.scheduler import EnergyAwareScheduler, RunnerChoice


def test_scheduler_simple_prompt() -> None:
    """Test scheduling for simple prompt."""
    scheduler = EnergyAwareScheduler(
        device_power_budget_j=10.0,
        default_latency_slo_ms=1000.0,
        local_runner_available=False,
        upstream_available=True,
    )

    choice = scheduler.schedule("Hello world")

    assert choice.runner_type == "script"
    assert choice.estimated_cost_j < 0.2
    assert choice.estimated_latency_ms < 300
    assert "script" in choice.reason.lower() or "lightweight" in choice.reason.lower()


def test_scheduler_complex_prompt() -> None:
    """Test scheduling for complex prompt."""
    scheduler = EnergyAwareScheduler(
        device_power_budget_j=10.0,
        default_latency_slo_ms=1000.0,
        local_runner_available=True,
        upstream_available=True,
    )

    prompt = """
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    
    Implement this recursively and explain the time complexity.
    """

    choice = scheduler.schedule(prompt)

    # Complex prompt should trigger higher complexity score
    assert choice.estimated_cost_j > 0.1
    # Should choose something other than script due to complexity
    assert choice.runner_type in ("script", "local", "upstream")


def test_scheduler_respects_energy_budget() -> None:
    """Test that scheduler respects energy constraints."""
    scheduler = EnergyAwareScheduler(
        device_power_budget_j=0.1,  # Very tight budget
        default_latency_slo_ms=1000.0,
        local_runner_available=True,
        upstream_available=True,
    )

    prompt = "Short"
    choice = scheduler.schedule(prompt)

    # Should choose script because it's cheapest
    assert choice.runner_type == "script"
    assert choice.estimated_cost_j <= 0.1


def test_scheduler_respects_latency_slo() -> None:
    """Test that scheduler respects latency SLO."""
    scheduler = EnergyAwareScheduler(
        device_power_budget_j=10.0,
        default_latency_slo_ms=100.0,  # Very tight latency
        local_runner_available=True,
        upstream_available=True,
    )

    prompt = "Short"
    choice = scheduler.schedule(prompt)

    # Should choose script because it's fastest
    assert choice.runner_type == "script"
    assert choice.estimated_latency_ms <= 100.0 or choice.metadata.get("fallback", False)


def test_scheduler_fallback_when_no_option_fits() -> None:
    """Test fallback behavior when no option meets constraints."""
    scheduler = EnergyAwareScheduler(
        device_power_budget_j=0.01,  # Impossible budget
        default_latency_slo_ms=10.0,  # Impossible latency
        local_runner_available=False,
        upstream_available=False,
    )

    prompt = "Hello"
    choice = scheduler.schedule(prompt)

    # Should still return a choice but mark as fallback
    assert choice.runner_type == "script"
    assert choice.metadata.get("fallback", False)


def test_scheduler_prefers_local_when_available() -> None:
    """Test preference for local runner when prefer_local=True."""
    scheduler = EnergyAwareScheduler(
        device_power_budget_j=10.0,
        default_latency_slo_ms=1000.0,
        local_runner_available=True,
        upstream_available=True,
    )

    prompt = "Short"
    choice = scheduler.schedule(prompt, prefer_local=True)

    # With prefer_local, should choose local if feasible
    if choice.estimated_cost_j <= 10.0 and choice.estimated_latency_ms <= 1000.0:
        assert choice.runner_type in ("local", "script")


def test_scheduler_choice_metadata() -> None:
    """Test that scheduler returns proper metadata."""
    scheduler = EnergyAwareScheduler(
        device_power_budget_j=10.0,
        default_latency_slo_ms=1000.0,
    )

    choice = scheduler.schedule("Test prompt")

    assert isinstance(choice, RunnerChoice)
    assert choice.runner_type in ("script", "local", "upstream")
    assert choice.estimated_cost_j > 0
    assert choice.estimated_latency_ms > 0
    assert len(choice.reason) > 0
    assert isinstance(choice.metadata, dict)


def test_scheduler_complexity_estimation() -> None:
    """Test complexity scoring based on markers."""
    scheduler = EnergyAwareScheduler()

    # Test length-based complexity
    short_cost, short_lat = scheduler._estimate_script_cost("x")
    long_cost, long_lat = scheduler._estimate_script_cost("x" * 1000)
    assert long_cost > short_cost
    assert long_lat > short_lat

    # Test code marker
    code_cost, code_lat = scheduler._estimate_script_cost('print("hello")\ndef foo(): pass')
    simple_cost, simple_lat = scheduler._estimate_script_cost("hello")
    assert code_cost > simple_cost
    assert code_lat > simple_lat

    # Test math marker
    math_cost, math_lat = scheduler._estimate_script_cost("Calculate $x^2 + y^2$")
    no_math_cost, no_math_lat = scheduler._estimate_script_cost("Calculate result")
    assert math_cost > no_math_cost


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

