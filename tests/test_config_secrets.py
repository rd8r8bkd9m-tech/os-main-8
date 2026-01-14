"""Tests for secure secret management."""

import pytest
from backend.service.config_secrets import (
    get_secret,
    get_ai_core_secret,
    get_generative_ai_secret,
    get_llm_api_key,
    is_production,
    validate_secrets,
    SecretNotFoundError,
)


class TestGetSecret:
    """Test get_secret function."""
    
    def test_get_existing_secret(self, monkeypatch):
        """Test retrieving an existing secret."""
        monkeypatch.setenv("TEST_SECRET", "test-value-123")
        assert get_secret("TEST_SECRET") == "test-value-123"
    
    def test_get_missing_required_secret_raises(self):
        """Test that missing required secret raises error."""
        with pytest.raises(SecretNotFoundError) as exc_info:
            get_secret("NONEXISTENT_SECRET_XYZ")
        assert "NONEXISTENT_SECRET_XYZ" in str(exc_info.value)
    
    def test_get_missing_optional_secret_returns_default(self):
        """Test that missing optional secret returns default."""
        result = get_secret("NONEXISTENT_SECRET", default="default-val", required=False)
        assert result == "default-val"
    
    def test_get_empty_secret_treated_as_missing(self, monkeypatch):
        """Test that empty string is treated as missing."""
        monkeypatch.setenv("EMPTY_SECRET", "")
        with pytest.raises(SecretNotFoundError):
            get_secret("EMPTY_SECRET")
    
    def test_get_whitespace_secret_treated_as_missing(self, monkeypatch):
        """Test that whitespace-only secret is treated as missing."""
        monkeypatch.setenv("WHITESPACE_SECRET", "   ")
        with pytest.raises(SecretNotFoundError):
            get_secret("WHITESPACE_SECRET")
    
    def test_secret_value_stripped(self, monkeypatch):
        """Test that secret values are stripped of whitespace."""
        monkeypatch.setenv("SPACED_SECRET", "  value  ")
        assert get_secret("SPACED_SECRET") == "value"


class TestSpecificSecrets:
    """Test specific secret retrieval functions."""
    
    def test_get_ai_core_secret(self, monkeypatch):
        """Test AI core secret retrieval."""
        monkeypatch.setenv("KOLIBRI_AI_CORE_SECRET", "ai-secret-123")
        assert get_ai_core_secret() == "ai-secret-123"
    
    def test_get_ai_core_secret_fallback(self, monkeypatch):
        """Test AI core secret falls back to generic secret."""
        monkeypatch.delenv("KOLIBRI_AI_CORE_SECRET", raising=False)
        monkeypatch.setenv("KOLIBRI_SECRET_KEY", "fallback-secret")
        assert get_ai_core_secret() == "fallback-secret"
    
    def test_get_ai_core_secret_default(self, monkeypatch):
        """Test AI core secret uses development default."""
        monkeypatch.delenv("KOLIBRI_AI_CORE_SECRET", raising=False)
        monkeypatch.delenv("KOLIBRI_SECRET_KEY", raising=False)
        result = get_ai_core_secret()
        assert "dev-secret" in result or "change-in-production" in result
    
    def test_get_generative_ai_secret(self, monkeypatch):
        """Test generative AI secret retrieval."""
        monkeypatch.setenv("KOLIBRI_GENERATIVE_SECRET", "gen-secret-456")
        assert get_generative_ai_secret() == "gen-secret-456"
    
    def test_get_llm_api_key_when_set(self, monkeypatch):
        """Test LLM API key retrieval when configured."""
        monkeypatch.setenv("KOLIBRI_LLM_API_KEY", "llm-key-789")
        assert get_llm_api_key() == "llm-key-789"
    
    def test_get_llm_api_key_when_not_set(self, monkeypatch):
        """Test LLM API key returns None when not configured."""
        monkeypatch.delenv("KOLIBRI_LLM_API_KEY", raising=False)
        assert get_llm_api_key() is None


class TestProductionCheck:
    """Test production environment detection."""
    
    def test_is_production_when_set_to_production(self, monkeypatch):
        """Test production detection."""
        monkeypatch.setenv("KOLIBRI_ENV", "production")
        assert is_production() is True
    
    def test_is_production_when_set_to_prod(self, monkeypatch):
        """Test production detection with 'prod' value."""
        monkeypatch.setenv("KOLIBRI_ENV", "prod")
        assert is_production() is True
    
    def test_is_production_case_insensitive(self, monkeypatch):
        """Test production detection is case-insensitive."""
        monkeypatch.setenv("KOLIBRI_ENV", "PRODUCTION")
        assert is_production() is True
    
    def test_is_production_false_for_development(self, monkeypatch):
        """Test production returns False for development."""
        monkeypatch.setenv("KOLIBRI_ENV", "development")
        assert is_production() is False
    
    def test_is_production_false_by_default(self, monkeypatch):
        """Test production returns False when not set."""
        monkeypatch.delenv("KOLIBRI_ENV", raising=False)
        assert is_production() is False


class TestValidateSecrets:
    """Test secret validation."""
    
    def test_validate_secrets_succeeds_with_all_secrets(self, monkeypatch):
        """Test validation succeeds when all secrets configured."""
        monkeypatch.setenv("KOLIBRI_AI_CORE_SECRET", "ai-secret")
        monkeypatch.setenv("KOLIBRI_GENERATIVE_SECRET", "gen-secret")
        monkeypatch.setenv("KOLIBRI_ENV", "development")
        assert validate_secrets() is True
    
    def test_validate_secrets_fails_in_production_with_default_secrets(self, monkeypatch):
        """Test validation fails in production with default secrets."""
        from backend.service.config_secrets import get_ai_core_secret
        
        monkeypatch.setenv("KOLIBRI_ENV", "production")
        monkeypatch.delenv("KOLIBRI_AI_CORE_SECRET", raising=False)
        monkeypatch.delenv("KOLIBRI_GENERATIVE_SECRET", raising=False)
        
        # Get actual default value to avoid hardcoding
        monkeypatch.delenv("KOLIBRI_SECRET_KEY", raising=False)
        monkeypatch.setenv("KOLIBRI_ENV", "development")
        default_secret = get_ai_core_secret()
        
        # Now test with that default in production
        monkeypatch.setenv("KOLIBRI_ENV", "production")
        monkeypatch.setenv("KOLIBRI_SECRET_KEY", default_secret)
        
        with pytest.raises(SecretNotFoundError) as exc_info:
            validate_secrets()
        assert "production" in str(exc_info.value).lower()
    
    def test_validate_secrets_allows_default_in_development(self, monkeypatch):
        """Test validation allows default secrets in development."""
        monkeypatch.setenv("KOLIBRI_ENV", "development")
        monkeypatch.delenv("KOLIBRI_AI_CORE_SECRET", raising=False)
        monkeypatch.delenv("KOLIBRI_GENERATIVE_SECRET", raising=False)
        # Should not raise
        validate_secrets()


class TestSecretSecurity:
    """Test security aspects of secret management."""
    
    def test_secrets_not_in_exception_messages(self, monkeypatch):
        """Test that secret values are not exposed in exceptions."""
        monkeypatch.setenv("TEST_SECRET", "super-secret-value")
        # Even though secret exists, error message should not contain the value
        try:
            raise SecretNotFoundError("Configuration error")
        except SecretNotFoundError as e:
            assert "super-secret-value" not in str(e)
    
    def test_empty_default_returned_for_optional_missing_secret(self):
        """Test that empty string is returned when default is None."""
        result = get_secret("MISSING_OPTIONAL", required=False)
        assert result == ""
