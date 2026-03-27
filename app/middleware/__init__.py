"""
Middleware Package

Centralized middleware registration for Aldudu Academy.
"""

from .tenant import register_tenant_middleware, invalidate_school_cache
from .request_id import register_request_id
from .logging import register_request_logging
from .security import register_security_middleware

__all__ = [
    'register_tenant_middleware',
    'register_request_id',
    'register_request_logging',
    'register_security_middleware',
    'register_all_middleware',
    'invalidate_school_cache',
]


def register_all_middleware(app):
    """
    Register all middleware components.

    Order matters:
    1. Request ID - for tracing
    2. Request Logging - for performance monitoring
    3. Tenant Resolution - for multi-tenancy
    4. Security - for security headers and validation
    """
    register_request_id(app)
    register_request_logging(app)
    register_tenant_middleware(app)
    register_security_middleware(app)


# Backward compatibility alias
register_middleware = register_all_middleware
