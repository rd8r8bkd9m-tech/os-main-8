"""Test suite for Kolibri AI Core reasoning engine."""
import asyncio
import pytest

from backend.service.ai_core import (
    KolibriAICore,
    KolibriAIDecision,
    InferenceMode,
)


class TestKolibriAICore:
    """Test Kolibri AI Core functionality."""

    @pytest.fixture
    def ai_core(self):
        """Create AI core instance for testing."""
        return KolibriAICore(
            secret_key="test-secret",
            enable_llm=False,
            llm_endpoint=None,
        )

    @pytest.mark.asyncio
    async def test_reason_symbolic_only(self, ai_core):
        """Test symbolic reasoning path."""
        query = "What is 2 + 2?"
        decision = await ai_core.reason(query)

        assert isinstance(decision, KolibriAIDecision)
        assert decision.query == query
        assert decision.response is not None
        assert len(decision.response) > 0
        assert decision.confidence >= 0.0 and decision.confidence <= 1.0
        assert decision.mode in [InferenceMode.SCRIPT, InferenceMode.HYBRID]
        assert decision.energy_cost_j > 0
        assert decision.signature is not None
        assert decision.reasoning_trace is not None

    @pytest.mark.asyncio
    async def test_reason_verifiable_signature(self, ai_core):
        """Test cryptographic signature verification."""
        query = "Test query"
        decision = await ai_core.reason(query)

        # Test verification method
        verified = decision.verify_signature("test-secret")
        assert verified is True

        # Test with wrong key
        not_verified = decision.verify_signature("wrong-key")
        assert not_verified is False

    @pytest.mark.asyncio
    async def test_reasoning_trace_structure(self, ai_core):
        """Test reasoning trace contains steps."""
        query = "How tall is a giraffe?"
        decision = await ai_core.reason(query)

        assert isinstance(decision.reasoning_trace, list)
        assert len(decision.reasoning_trace) > 0

        for step in decision.reasoning_trace:
            assert isinstance(step, dict)
            assert len(step) > 0  # Each step has data

    @pytest.mark.asyncio
    async def test_batch_reasoning(self, ai_core):
        """Test concurrent batch processing."""
        queries = [
            "Query 1",
            "Query 2",
            "Query 3",
        ]

        decisions = await ai_core.batch_reason(queries)

        assert len(decisions) == len(queries)
        for i, decision in enumerate(decisions):
            assert decision.query == queries[i]
            assert decision.response is not None
            assert decision.signature is not None

    @pytest.mark.asyncio
    async def test_energy_tracking(self, ai_core):
        """Test energy cost calculation."""
        query1 = "Short"
        query2 = "This is a much longer query to test energy calculation"

        decision1 = await ai_core.reason(query1)
        energy1 = decision1.energy_cost_j

        decision2 = await ai_core.reason(query2)
        energy2 = decision2.energy_cost_j

        # Both should use positive energy
        assert energy1 > 0
        assert energy2 > 0

    @pytest.mark.asyncio
    async def test_mode_routing(self, ai_core):
        """Test inference mode routing decision."""
        # Short query should prefer script (lower energy)
        short_query = "x"
        decision_short = await ai_core.reason(short_query)
        assert decision_short.mode in [InferenceMode.SCRIPT, InferenceMode.LOCAL_LLM]

        # Complex query might prefer hybrid if LLM available
        complex_query = "Explain the relationship between energy, mass, and the speed of light"
        decision_complex = await ai_core.reason(complex_query)
        assert decision_complex.mode in [InferenceMode.SCRIPT, InferenceMode.HYBRID, InferenceMode.LOCAL_LLM]

    @pytest.mark.asyncio
    async def test_stats_aggregation(self, ai_core):
        """Test statistics tracking."""
        await ai_core.reason("Query 1")
        await ai_core.reason("Query 2")

        stats = ai_core.get_stats()

        assert stats["total_queries"] == 2
        assert stats["total_energy_j"] > 0
        assert "avg_energy_per_query_j" in stats
        assert "mode" in stats
        assert "avg_latency_ms" not in stats or stats.get("avg_latency_ms", 0) >= 0

    @pytest.mark.asyncio
    async def test_offline_operation(self, ai_core):
        """Test that AI works without external connections."""
        # This should not raise any connection errors
        query = "Test offline operation"
        decision = await ai_core.reason(query)

        assert decision is not None
        assert decision.response is not None

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, ai_core):
        """Test concurrent reasoning requests."""
        async def make_request(query):
            return await ai_core.reason(query)

        tasks = [
            make_request("Query A"),
            make_request("Query B"),
            make_request("Query C"),
            make_request("Query D"),
        ]

        decisions = await asyncio.gather(*tasks)

        assert len(decisions) == 4
        for decision in decisions:
            assert decision.signature is not None
            assert decision.response is not None

    def test_decision_dataclass_fields(self):
        """Test KolibriAIDecision dataclass structure."""
        decision = KolibriAIDecision(
            query="Test",
            response="Response",
            confidence=0.95,
            reasoning_trace=[{"phase": "symbolic", "result": "processed"}],
            signature="sig123",
            mode=InferenceMode.SCRIPT,
            energy_cost_j=0.05,
            decision_time_ms=150,
        )

        assert decision.query == "Test"
        assert decision.response == "Response"
        assert decision.confidence == 0.95
        assert decision.mode == InferenceMode.SCRIPT

    def test_inference_mode_enum(self):
        """Test InferenceMode enum values."""
        assert InferenceMode.SCRIPT.value == "script"
        assert InferenceMode.LOCAL_LLM.value == "local_llm"
        assert InferenceMode.HYBRID.value == "hybrid"

    @pytest.mark.asyncio
    async def test_response_determinism(self, ai_core):
        """Test that symbolic reasoning is deterministic."""
        query = "What is 2 + 2?"

        decision1 = await ai_core.reason(query)
        decision2 = await ai_core.reason(query)

        # Symbolic path should produce same response
        assert decision1.response == decision2.response
        assert decision1.confidence == decision2.confidence

    @pytest.mark.asyncio
    async def test_hybrid_mode_uses_neural_engine(self):
        """Ensure hybrid mode produces enriched neural context."""
        ai_core = KolibriAICore(
            secret_key="hybrid-secret",
            enable_llm=True,
        )

        query = "Hey Kolibri team, great to meet you!"
        decision = await ai_core.reason(query)

        assert decision.mode == InferenceMode.HYBRID
        assert "Kolibri" in decision.response
        assert "Additional context" in decision.response
        assert decision.energy_cost_j >= 0.4

        stages = {step.get("stage") for step in decision.reasoning_trace if isinstance(step, dict)}
        assert "neural_inference" in stages
        assert "prompt_selection" in stages

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, ai_core):
        """Test confidence scoring in decisions."""
        queries = [
            "1 + 1 = ?",  # Simple, should have high confidence
            "What is the meaning of life?",  # Complex, might have lower confidence
        ]

        for query in queries:
            decision = await ai_core.reason(query)
            assert 0.0 <= decision.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_knowledge_graph_enrichment(self, ai_core):
        """Ensure knowledge graph insights enrich responses."""

        query = "Need insight on MAU conversion funnel health"
        decision = await ai_core.reason(query)

        assert "Insight:" in decision.response
        assert "Knowledge summary" in decision.response
        assert any(
            step.get("stage") == "knowledge_retrieval"
            for step in decision.reasoning_trace
            if isinstance(step, dict)
        )
        assert any(
            step.get("stage") == "knowledge_synthesis"
            for step in decision.reasoning_trace
            if isinstance(step, dict)
        )

    @pytest.mark.asyncio
    async def test_knowledge_graph_usage_stats(self, ai_core):
        """Knowledge graph stats should track query insights."""

        query = "Need insight on MAU conversion funnel health"
        await ai_core.reason(query)

        stats = ai_core.get_stats()
        knowledge_stats = stats.get("knowledge_graph", {})

        assert knowledge_stats.get("queries_with_matches", 0) >= 1
        assert knowledge_stats.get("last_entities")
        top_entities = knowledge_stats.get("top_entities", [])
        assert top_entities and isinstance(top_entities[0], tuple)
        assert knowledge_stats.get("last_keywords")

    @pytest.mark.asyncio
    async def test_error_recovery(self, ai_core):
        """Test graceful error handling."""
        # Test with various edge cases
        edge_cases = [
            "",  # Empty query
            "x" * 10000,  # Very long query
            "!@#$%^&*()",  # Special characters
        ]

        for query in edge_cases:
            try:
                decision = await ai_core.reason(query)
                # Should return valid decision or raise informative error
                assert decision is not None
            except ValueError as e:
                # Expected for some edge cases
                assert str(e)


class TestInferenceModeRouting:
    """Test inference mode routing logic."""

    @pytest.fixture
    def ai_core(self):
        return KolibriAICore(
            secret_key="test",
            enable_llm=True,
            llm_endpoint="http://localhost:11434",
        )

    @pytest.mark.asyncio
    async def test_routing_decision_logic(self, ai_core):
        """Test routing decision for mode selection."""
        # This tests the internal routing logic
        short_query = "hi"
        mode, budget = await ai_core._decide_routing(short_query)

        assert mode in [InferenceMode.SCRIPT, InferenceMode.LOCAL_LLM, InferenceMode.HYBRID]
        assert budget > 0


class TestSymbolicReasoning:
    """Test symbolic reasoning component."""

    @pytest.fixture
    def ai_core(self):
        return KolibriAICore(
            secret_key="test",
            enable_llm=False,
        )

    @pytest.mark.asyncio
    async def test_symbolic_reasoning_outputs(self, ai_core):
        """Test symbolic reasoning produces valid outputs."""
        query = "What color is the sky?"
        response, trace, energy = ai_core._apply_symbolic_reasoning(query)

        assert isinstance(response, str)
        assert len(response) > 0
        assert isinstance(trace, list)  # Returns list of trace steps
        assert isinstance(energy, float)
        assert energy > 0


# Integration tests
class TestIntegration:
    """Integration tests for Kolibri AI."""

    @pytest.mark.asyncio
    async def test_full_reasoning_pipeline(self):
        """Test complete reasoning pipeline."""
        ai_core = KolibriAICore(
            secret_key="integration-test",
            enable_llm=False,
        )

        queries = [
            "Simple math: 5 * 5 = ?",
            "What are the three laws of thermodynamics?",
            "How does photosynthesis work?",
        ]

        for query in queries:
            decision = await ai_core.reason(query)

            # Verify all components are present
            assert decision.query == query
            assert decision.response
            assert decision.confidence >= 0
            assert decision.signature
            assert decision.reasoning_trace
            assert decision.energy_cost_j > 0

            # Verify signature
            assert decision.verify_signature("integration-test")

    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test that AI operates within performance targets."""
        ai_core = KolibriAICore(
            secret_key="perf-test",
            enable_llm=False,
        )

        query = "Performance test query"
        decision = await ai_core.reason(query)

        # Should complete in reasonable time
        assert decision.decision_time_ms < 5000, "Reasoning took too long"

        # Energy should be within reasonable bounds
        assert decision.energy_cost_j < 1.0, "Energy cost too high"
