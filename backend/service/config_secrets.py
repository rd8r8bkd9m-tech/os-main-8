"""Secure secret management for Kolibri AI.

This module provides environment-based secret management to eliminate
hardcoded credentials from source code.

Principles:
- Легкость: Simple interface with sensible defaults
- Точность: Type-safe secret retrieval  
- Безопасность: Never log or expose secrets
"""

import os
from typing import Optional


class SecretNotFoundError(Exception):
    """Raised when a required secret is not configured."""
    pass


def get_secret(
    key: str,
    default: Optional[str] = None,
    required: bool = True
) -> str:
    """Retrieve a secret from environment variables.
    
    Args:
        key: Environment variable name
        default: Default value if not found (only used if required=False)
        required: If True, raises SecretNotFoundError when secret missing
        
    Returns:
        Secret value from environment
        
    Raises:
        SecretNotFoundError: If required=True and secret not found
        
    Example:
        >>> api_key = get_secret("KOLIBRI_API_KEY")
        >>> optional_key = get_secret("DEBUG_KEY", default="", required=False)
        
    Security:
        - Never logs secret values
        - Uses environment variables only (no files)
        - Validates non-empty values
    """
    value = os.environ.get(key)
    
    if value is None or value.strip() == "":
        if required:
            raise SecretNotFoundError(
                f"Required secret '{key}' not found in environment. "
                f"Please set the {key} environment variable."
            )
        return default or ""
        
    return value.strip()


def get_ai_core_secret() -> str:
    """Get AI Core secret key.
    
    Returns:
        Secret key for AI Core HMAC signatures
        
    Environment:
        KOLIBRI_AI_CORE_SECRET: Main secret (required)
        KOLIBRI_SECRET_KEY: Fallback secret
    """
    try:
        return get_secret("KOLIBRI_AI_CORE_SECRET")
    except SecretNotFoundError:
        # Fallback to generic secret for backward compatibility
        return get_secret(
            "KOLIBRI_SECRET_KEY",
            default="kolibri-dev-secret-change-in-production"
        )


def get_generative_ai_secret() -> str:
    """Get Generative AI secret key.
    
    Returns:
        Secret key for Generative AI system
        
    Environment:
        KOLIBRI_GENERATIVE_SECRET: Main secret (required)
        KOLIBRI_SECRET_KEY: Fallback secret
    """
    try:
        return get_secret("KOLIBRI_GENERATIVE_SECRET")
    except SecretNotFoundError:
        # Fallback to generic secret for backward compatibility
        return get_secret(
            "KOLIBRI_SECRET_KEY",
            default="kolibri-generative-dev-secret-change-in-production"
        )


def get_llm_api_key() -> Optional[str]:
    """Get LLM API key if configured.
    
    Returns:
        LLM API key or None if not configured
        
    Environment:
        KOLIBRI_LLM_API_KEY: Optional LLM provider API key
    """
    return get_secret("KOLIBRI_LLM_API_KEY", default=None, required=False)


def is_production() -> bool:
    """Check if running in production environment.
    
    Returns:
        True if KOLIBRI_ENV=production, False otherwise
    """
    env = os.environ.get("KOLIBRI_ENV", "development").lower()
    return env in ("production", "prod")


def validate_secrets() -> bool:
    """Validate that all required secrets are configured.
    
    Returns:
        True if all secrets are valid
        
    Raises:
        SecretNotFoundError: If any required secret is missing
        
    Usage:
        Call during application startup to fail fast if secrets are missing.
        
        >>> if __name__ == "__main__":
        >>>     validate_secrets()  # Will raise if misconfigured
        >>>     start_application()
    """
    # Required secrets
    get_ai_core_secret()
    get_generative_ai_secret()
    
    # Warn if using default secrets in production
    if is_production():
        ai_secret = get_ai_core_secret()
        if "dev-secret" in ai_secret or "change-in-production" in ai_secret:
            raise SecretNotFoundError(
                "Default development secrets detected in production environment! "
                "Please configure KOLIBRI_AI_CORE_SECRET and "
                "KOLIBRI_GENERATIVE_SECRET with secure values."
            )
    
    return True
