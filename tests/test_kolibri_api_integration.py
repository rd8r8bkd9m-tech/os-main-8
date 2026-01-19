"""Integration tests for Kolibri AI API endpoints."""
import pytest


@pytest.fixture
def client():
    """Create test client."""
    from fastapi import FastAPI
    from backend.service.routes.inference import router
    
    app = FastAPI()
    app.include_router(router)
    
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestKolibriAIEndpoints:
    """Test Kolibri AI API endpoints."""

    def test_api_imports(self):
        """Test that AI core is properly integrated into API."""
        from backend.service.routes.inference import _ai_core, KolibriAICore
        
        assert _ai_core is not None
        assert isinstance(_ai_core, KolibriAICore)
        assert _ai_core.enable_llm is False  # Default: offline


class TestKolibriAIIntegration:
    """Test full integration of Kolibri AI."""

    @pytest.mark.asyncio
    async def test_ai_core_integration(self):
        """Test AI core is accessible and working."""
        from backend.service.routes.inference import _ai_core

        # Execute reasoning
        decision = await _ai_core.reason("What is 2+2?")
        
        # Verify response
        assert decision.query == "What is 2+2?"
        assert decision.response is not None
        assert len(decision.response) > 0
        assert decision.signature is not None
        
        # Verify signature (uses default secret from config_secrets)
        from backend.service.config_secrets import get_ai_core_secret
        assert decision.verify_signature(get_ai_core_secret())

    @pytest.mark.asyncio
    async def test_batch_api_integration(self):
        """Test batch reasoning integration."""
        from backend.service.routes.inference import _ai_core

        queries = ["What is A?", "What is B?", "What is C?"]
        decisions = await _ai_core.batch_reason(queries)
        
        assert len(decisions) == 3
        from backend.service.config_secrets import get_ai_core_secret
        for decision in decisions:
            assert decision.signature is not None
            assert decision.verify_signature(get_ai_core_secret())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
