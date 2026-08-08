"""
Environment Variable Validation
Validates required environment variables at application startup.
"""
import os
import warnings
from typing import List, Optional


class EnvironmentValidationError(Exception):
    """Raised when environment validation fails"""
    pass


def validate_env_vars(testing: bool = False) -> None:
    """
    Validate required environment variables.
    
    Args:
        testing: If True, relax some requirements for test environment
        
    Raises:
        EnvironmentValidationError: If critical variables are missing
    """
    errors: List[str] = []
    warnings_list: List[str] = []
    
    # Critical variables (required for all environments)
    critical_vars = {
        'SECRET_KEY': 'Application secret key for session management',
        'DATABASE_URL': 'Database connection URL',
    }
    
    # Important variables (should be set, but app can start without them)
    important_vars = {
        'MAIL_SERVER': 'SMTP server for sending emails',
        'MAIL_USERNAME': 'SMTP username',
        'MAIL_PASSWORD': 'SMTP password',
        'CELERY_BROKER_URL': 'Redis URL for Celery broker',
    }
    
    # Check critical variables
    for var, description in critical_vars.items():
        if not os.environ.get(var):
            if testing:
                warnings_list.append(f"Missing {var}: {description}")
            else:
                errors.append(f"Missing {var}: {description}")
    
    # Check important variables (warnings only)
    for var, description in important_vars.items():
        if not os.environ.get(var):
            warnings_list.append(f"Missing {var}: {description}")
    
    # Validate SECRET_KEY strength
    secret_key = os.environ.get('SECRET_KEY', '')
    if secret_key and len(secret_key) < 32:
        warnings_list.append("SECRET_KEY is too short (should be at least 32 characters)")
    
    # Validate DATABASE_URL format
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url:
        valid_prefixes = ['mysql', 'postgresql', 'sqlite']
        if not any(database_url.startswith(prefix) for prefix in valid_prefixes):
            errors.append(f"Invalid DATABASE_URL format. Should start with one of: {valid_prefixes}")
    
    # Validate CACHE_TYPE if set
    cache_type = os.environ.get('CACHE_TYPE', 'SimpleCache')
    if cache_type == 'RedisCache':
        redis_host = os.environ.get('CACHE_REDIS_HOST')
        if not redis_host:
            warnings_list.append("CACHE_TYPE is RedisCache but CACHE_REDIS_HOST not set")
    
    # Raise errors if any
    if errors:
        raise EnvironmentValidationError(
            f"Environment validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )
    
    # Show warnings
    for warning in warnings_list:
        warnings.warn(warning, UserWarning)


def validate_upload_config() -> None:
    """Validate file upload configuration"""
    max_content_length = os.environ.get('MAX_CONTENT_LENGTH', '16777216')
    
    try:
        max_bytes = int(max_content_length)
        if max_bytes > 100 * 1024 * 1024:  # 100MB
            warnings.warn(
                f"MAX_CONTENT_LENGTH is very large ({max_bytes} bytes). "
                "Consider reducing to prevent memory issues.",
                UserWarning
            )
    except ValueError:
        warnings.warn(f"Invalid MAX_CONTENT_LENGTH: {max_content_length}", UserWarning)


def validate_sentry_config() -> None:
    """Validate Sentry configuration if enabled"""
    sentry_dsn = os.environ.get('SENTRY_DSN')
    
    if sentry_dsn:
        # Check if DSN looks valid
        if not sentry_dsn.startswith('https://'):
            warnings.warn(
                "SENTRY_DSN should start with 'https://'. "
                "Check your Sentry configuration.",
                UserWarning
            )
        
        # Check for placeholder values
        if 'your-sentry-dsn' in sentry_dsn.lower():
            warnings.warn(
                "SENTRY_DSN appears to be a placeholder. "
                "Update with your actual Sentry DSN.",
                UserWarning
            )


def run_all_validations(testing: bool = False) -> None:
    """
    Run all environment validations.
    
    Args:
        testing: If True, relax some requirements for test environment
    """
    validate_env_vars(testing=testing)
    validate_upload_config()
    validate_sentry_config()
